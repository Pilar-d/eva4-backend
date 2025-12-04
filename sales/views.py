# sales/views.py

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
# ⚠️ CORRECCIÓN 1: Importar Count aquí para uso en sales_report.
from django.db.models import Sum, F, Count 
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework.exceptions import PermissionDenied, ValidationError # Added missing DRF exceptions

# Importar modelos, serializadores y permisos locales
from .models import Sale, SaleItem, Order, OrderItem, CartItem
from .serializers import SaleSerializer, PurchaseCreateSerializer, CartItemSerializer, OrderSerializer
from products.models import Branch, Product, Inventory, Supplier
from accounts.permissions import IsVendedor, IsAdminClienteOrGerente

# ----------------------------------------------------
# A. Ventas POS
# ----------------------------------------------------

class SaleViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Registro y listado (Reportes) de ventas POS.
    """
    queryset = Sale.objects.all().select_related('branch', 'user')
    serializer_class = SaleSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            # POST /api/sales/ solo para vendedores
            return [IsAuthenticated(), IsVendedor()]
        if self.action == 'list':
            # GET /api/sales/ (reportes) solo para gerentes/admin
            return [IsAuthenticated(), IsAdminClienteOrGerente()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filtra las ventas por la compañía del usuario (tenancy) y filtros de reporte."""
        user = self.request.user
        if not user.company:
            return Sale.objects.none()

        queryset = super().get_queryset().filter(branch__company=user.company)
        
        # Lógica de Filtrado (Reportes mínimos)
        branch_id = self.request.query_params.get('branch')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            # Incluir hasta el final del día
            queryset = queryset.filter(created_at__date__lte=date_to) 
            
        return queryset

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        POST /api/sales/ - Registra la venta POS y actualiza el inventario.
        """
        serializer = SaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        branch = serializer.validated_data['branch']
        sale_items_data = serializer.validated_data.pop('items')
        
        # 1. Validación de Pertenencia y Rol (Tenancy)
        if branch.company != request.user.company:
            raise PermissionDenied("La sucursal no pertenece a tu compañía.")
        if request.user.role != 'vendedor':
             raise PermissionDenied("Solo los vendedores pueden registrar ventas POS.")

        # 2. Calcular total y verificar stock
        calculated_total = 0
        sale_items_to_create = []
        
        for item_data in sale_items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            price = item_data['price'] # Precio de venta al momento
            
            # Obtener stock
            try:
                inventory_item = Inventory.objects.get(product=product, branch=branch)
            except Inventory.DoesNotExist:
                raise Http404(f"Producto {product.name} no encontrado en el inventario de la sucursal.")

            if inventory_item.stock < quantity:
                raise ValidationError(f"Stock insuficiente para {product.name}. Solo hay {inventory_item.stock}.")

            calculated_total += price * quantity
            sale_items_to_create.append(item_data)
        
        # 3. Crear el objeto Sale
        sale = Sale.objects.create(
            user=request.user,
            total=calculated_total,
            **serializer.validated_data
        )

        # 4. Crear los ítems de venta y reducir el stock
        for item_data in sale_items_to_create:
            SaleItem.objects.create(sale=sale, **item_data)
            Inventory.objects.filter(product=item_data['product'], branch=branch).update(stock=F('stock') - item_data['quantity'])

        # 5. Respuesta
        response_serializer = SaleSerializer(sale)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# ----------------------------------------------------
# B. Compras / Ingreso de Stock
# ----------------------------------------------------

class PurchaseViewSet(viewsets.GenericViewSet):
    """
    POST /api/purchases/ - Registra una compra a proveedor e incrementa stock.
    """
    permission_classes = [IsAuthenticated, IsAdminClienteOrGerente]

    @transaction.atomic
    def create(self, request):
        serializer = PurchaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        supplier = get_object_or_404(Supplier, id=data['supplier_id'])
        branch = get_object_or_404(Branch, id=data['branch_id'])
        
        # Validación de Tenancy
        if supplier.company != request.user.company or branch.company != request.user.company:
             raise PermissionDenied("El proveedor o la sucursal no pertenece a tu compañía.")

        # Simulación de registro de la Orden de Compra (Purchase model no existe, se simula el movimiento)
        
        # 1. Procesar ítems y aumentar stock
        for item_data in data['items']:
            product = item_data['product']
            quantity = item_data['quantity']

            # Buscar o crear item de inventario
            inventory_item, created = Inventory.objects.get_or_create(
                product=product,
                branch=branch,
                defaults={'stock': 0, 'reorder_point': 0}
            )
            
            # Incrementar stock
            Inventory.objects.filter(id=inventory_item.id).update(stock=F('stock') + quantity)
            
            # Nota: Aquí se registraría el modelo Purchase y sus ítems si existieran.

        return Response({
            "detail": f"Ingreso de stock registrado con éxito en {branch.name} desde Proveedor: {supplier.name}.",
            "date": data['date']
        }, status=status.HTTP_201_CREATED)


# ----------------------------------------------------
# C. Carrito y Checkout (E-commerce API)
# ----------------------------------------------------

class CartViewSet(viewsets.GenericViewSet):
    """
    Manejo del carrito de compras vía API para E-commerce.
    """
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """POST /api/cart/add/ - Añadir producto al carro."""
        # Si el usuario no está autenticado, se podría usar la sesión, pero el requisito pide JWT.
        if not request.user.is_authenticated:
            return Response({"detail": "Se requiere autenticación para guardar el carrito."}, status=status.HTTP_401_UNAUTHORIZED)
            
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 1. Obtener o crear el CartItem
        item, created = CartItem.objects.get_or_create(
            user=request.user,
            product_id=serializer.validated_data['product'],
            defaults={'quantity': serializer.validated_data['quantity']}
        )
        
        if not created:
            # Si ya existe, incrementar la cantidad
            item.quantity += serializer.validated_data['quantity']
            item.save()

        return Response(CartItemSerializer(item).data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def checkout(self, request):
        """
        POST /api/cart/checkout/ - Convierte el carro en Order y vacía stock.
        """
        user = request.user
        
        # Si el usuario NO está logueado (cliente_final), se asume que los datos (email, name)
        # vienen en el request para crear la Order de forma anónima (opcional).
        
        # 1. Obtener ítems del carrito (asumimos usuario logueado)
        cart_items = CartItem.objects.filter(user=user).select_related('product')
        if not cart_items.exists():
            raise ValidationError("El carrito está vacío.")

        # 2. Determinar la compañía (tenant)
        # Asumimos que todos los productos son del mismo tenant para simplificar el E-commerce
        company = cart_items.first().product.company
        
        # 3. Calcular Total y Crear Order (lógica simplificada)
        total = sum(item.product.price * item.quantity for item in cart_items)

        order = Order.objects.create(
            company=company,
            cliente_final_name=user.get_full_name() or user.username,
            cliente_final_email=user.email,
            total=total,
            estado='PENDIENTE'
        )

        # 4. Crear OrderItems y reducir stock (de la Branch principal/default de la compañía)
        default_branch = company.branch_set.first()
        if not default_branch:
             raise Http404("La compañía no tiene una sucursal para despachar.")

        for item in cart_items:
            # Reducir stock
            Inventory.objects.filter(product=item.product, branch=default_branch).update(stock=F('stock') - item.quantity)

            # Crear OrderItem
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price # Precio al momento de la compra
            )
        
        # 5. Vaciar carrito
        cart_items.delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


# ----------------------------------------------------
# D. Reportes
# ----------------------------------------------------

class ReportViewSet(viewsets.GenericViewSet):
    """
    Vistas para generar reportes. Accesible por Admin Cliente y Gerente.
    """
    permission_classes = [IsAuthenticated, IsAdminClienteOrGerente]
    
    def get_queryset(self):
        user = self.request.user
        if user.company:
            return user.company
        raise PermissionDenied("Usuario sin compañía asignada.")

    @action(detail=False, methods=['get'])
    def stock_report(self, request):
        """
        GET /api/reports/stock/ - Reporte de stock por sucursal.
        """
        company = self.get_queryset()
        
        # Reporte de stock por sucursal
        report_data = Inventory.objects.filter(branch__company=company).values(
            'branch__name', 'product__name', 'stock', 'reorder_point'
        ).order_by('branch__name', 'product__name')
        
        return Response({
            "report_name": "Reporte de Stock por Sucursal",
            "company": company.name,
            "data": list(report_data)
        })

    @action(detail=False, methods=['get'])
    def sales_report(self, request):
        """
        GET /api/reports/sales/ - Reporte de ventas por periodo (día/mes) por sucursal.
        """
        company = self.get_queryset()
        
        # Filtros de ejemplo
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        branch_id = request.query_params.get('branch_id')
        
        sales_query = Sale.objects.filter(branch__company=company)
        
        if date_from:
            sales_query = sales_query.filter(created_at__date__gte=date_from)
        if date_to:
            sales_query = sales_query.filter(created_at__date__lte=date_to)
        if branch_id:
            sales_query = sales_query.filter(branch_id=branch_id)
            
        # Agrupación por día (ejemplo simple)
        report_data = sales_query.values(
            'branch__name',
        ).annotate(
            total_sales=Sum('total'),
            count=Count('id')
        ).order_by('-total_sales')
            
        return Response({
            "report_name": "Reporte de Ventas por Sucursal/Periodo",
            "company": company.name,
            "filters": {"from": date_from, "to": date_to, "branch_id": branch_id},
            "summary": list(report_data)
        })
    
    @transaction.atomic
    def create(self, request):
        # ... (Validación de headers/roles) ...
        
        # Reestructuración manual de ítems del formulario HTML
        form_data = request.data.copy()
        
        # Mapeamos los campos del formulario HTML al formato JSON esperado por el Serializer
        api_data = {
            'supplier_id': form_data.get('supplier_id'),
            'branch_id': form_data.get('branch_id'),
            'date': form_data.get('date'),
            'items': [
                {
                    'product': form_data.get('items-0-product'),
                    'quantity': form_data.get('items-0-quantity')
                    # Nota: El serializer de Purchase utiliza SaleItemSerializer, 
                    # que requiere 'price'. Tendrías que buscar el precio del producto
                    # antes de pasar los datos al serializer si el price es obligatorio.
                }
            ]
        }
        
        # ... (Continuar con la validación del serializer) ...
        # serializer = PurchaseCreateSerializer(data=api_data)
        # serializer.is_valid(raise_exception=True)
        # ... (El resto de la lógica de guardado) ...

        