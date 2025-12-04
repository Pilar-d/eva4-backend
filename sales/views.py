# sales/views.py

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Sum, F, Count # FIX: Importar Count, Sum, F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework.exceptions import PermissionDenied, ValidationError 

# Importar modelos y serializadores
from .models import Sale, SaleItem, Order, OrderItem, CartItem # Modelos locales
from .serializers import SaleSerializer, PurchaseCreateSerializer, CartItemSerializer, OrderSerializer
from products.models import Branch, Product, Inventory, Supplier # Modelos de Products
from accounts.models import User # Modelo User
from accounts.permissions import IsVendedor, IsAdminClienteOrGerente # Permisos

# ----------------------------------------------------
# A. Ventas POS (ViewSet)
# ----------------------------------------------------

class SaleViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Sale.objects.all().select_related('branch', 'user')
    serializer_class = SaleSerializer
    
    def get_permissions(self):
        if self.action == 'create': return [IsAuthenticated(), IsVendedor()]
        if self.action == 'list': return [IsAuthenticated(), IsAdminClienteOrGerente()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if not user.company: return Sale.objects.none()

        queryset = super().get_queryset().filter(branch__company=user.company)
        branch_id = self.request.query_params.get('branch'); date_from = self.request.query_params.get('date_from'); date_to = self.request.query_params.get('date_to')

        if branch_id: queryset = queryset.filter(branch_id=branch_id)
        if date_from: queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to: queryset = queryset.filter(created_at__date__lte=date_to) 
            
        return queryset

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = SaleSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        branch = serializer.validated_data['branch']; sale_items_data = serializer.validated_data.pop('items')
        
        if branch.company != request.user.company: raise PermissionDenied("La sucursal no pertenece a tu compañía.")
        if request.user.role != 'vendedor': raise PermissionDenied("Solo los vendedores pueden registrar ventas POS.")

        calculated_total = 0; sale_items_to_create = []
        
        for item_data in sale_items_data:
            product = item_data['product']; quantity = item_data['quantity']; price = item_data['price']
            
            try: inventory_item = Inventory.objects.get(product=product, branch=branch)
            except Inventory.DoesNotExist: raise Http404(f"Producto {product.name} no encontrado en el inventario de la sucursal.")

            if inventory_item.stock < quantity: raise ValidationError(f"Stock insuficiente para {product.name}. Solo hay {inventory_item.stock}.")

            calculated_total += price * quantity
            sale_items_to_create.append(item_data)
        
        sale = Sale.objects.create(user=request.user, total=calculated_total, **serializer.validated_data)

        for item_data in sale_items_to_create:
            SaleItem.objects.create(sale=sale, **item_data)
            Inventory.objects.filter(product=item_data['product'], branch=branch).update(stock=F('stock') - item_data['quantity'])

        response_serializer = SaleSerializer(sale)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# ----------------------------------------------------
# B. Compras / Ingreso de Stock (ViewSet)
# ----------------------------------------------------

class PurchaseViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsAdminClienteOrGerente]

    @transaction.atomic
    def create(self, request):
        serializer = PurchaseCreateSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        supplier = get_object_or_404(Supplier, id=data['supplier_id']); branch = get_object_or_404(Branch, id=data['branch_id'])
        
        if supplier.company != request.user.company or branch.company != request.user.company: raise PermissionDenied("El proveedor o la sucursal no pertenece a tu compañía.")

        for item_data in data['items']:
            product = item_data['product']; quantity = item_data['quantity']

            inventory_item, created = Inventory.objects.get_or_create(
                product=product, branch=branch, defaults={'stock': 0, 'reorder_point': 0}
            )
            Inventory.objects.filter(id=inventory_item.id).update(stock=F('stock') + quantity)
            
        return Response({"detail": f"Ingreso de stock registrado con éxito en {branch.name} desde Proveedor: {supplier.name}.",
                         "date": data['date']}, status=status.HTTP_201_CREATED)


# ----------------------------------------------------
# C. Carrito y Checkout (ViewSet)
# ----------------------------------------------------

class CartViewSet(viewsets.GenericViewSet):
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        if not request.user.is_authenticated: return Response({"detail": "Se requiere autenticación para guardar el carrito."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = CartItemSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        item, created = CartItem.objects.get_or_create(
            user=request.user, product_id=serializer.validated_data['product'],
            defaults={'quantity': serializer.validated_data['quantity']}
        )
        if not created: item.quantity += serializer.validated_data['quantity']; item.save()
        return Response(CartItemSerializer(item).data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def checkout(self, request):
        user = request.user
        cart_items = CartItem.objects.filter(user=user).select_related('product')
        if not cart_items.exists(): raise ValidationError("El carrito está vacío.")

        company = cart_items.first().product.company
        total = sum(item.product.price * item.quantity for item in cart_items)

        order = Order.objects.create(company=company, cliente_final_name=user.get_full_name() or user.username,
                                     cliente_final_email=user.email, total=total, estado='PENDIENTE')

        default_branch = company.branch_set.first()
        if not default_branch: raise Http404("La compañía no tiene una sucursal para despachar.")

        for item in cart_items:
            Inventory.objects.filter(product=item.product, branch=default_branch).update(stock=F('stock') - item.quantity)
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)
        
        cart_items.delete()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


# ----------------------------------------------------
# D. Reportes (ViewSet)
# ----------------------------------------------------

class ReportViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsAdminClienteOrGerente]
    
    def get_queryset(self):
        if self.request.user.company: return self.request.user.company
        raise PermissionDenied("Usuario sin compañía asignada.")

    @action(detail=False, methods=['get'])
    def stock_report(self, request):
        company = self.get_queryset()
        report_data = Inventory.objects.filter(branch__company=company).values(
            'branch__name', 'product__name', 'stock', 'reorder_point'
        ).order_by('branch__name', 'product__name')
        return Response({"report_name": "Reporte de Stock por Sucursal", "company": company.name, "data": list(report_data)})

    @action(detail=False, methods=['get'])
    def sales_report(self, request):
        company = self.get_queryset()
        date_from = request.query_params.get('date_from'); date_to = request.query_params.get('date_to'); branch_id = request.query_params.get('branch_id')
        sales_query = Sale.objects.filter(branch__company=company)
        
        if branch_id: sales_query = sales_query.filter(branch_id=branch_id)
        if date_from: sales_query = sales_query.filter(created_at__date__gte=date_from)
        if date_to: sales_query = sales_query.filter(created_at__date__lte=date_to)
            
        sales_query = sales_query.values('branch__name').annotate(total_sales=Sum('total'), count=Count('id')).order_by('-total_sales')
        return Response({"report_name": "Reporte de Ventas por Sucursal/Periodo", "company": company.name, 
                         "filters": {"from": date_from, "to": date_to, "branch_id": branch_id}, "summary": list(sales_query)})