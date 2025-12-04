# products/views.py (Django REST Framework Views)

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import F
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import transaction

# Importar modelos, serializadores y permisos locales (REAL IMPORTS)
from .models import Product, Branch, Supplier, Inventory
from .serializers import ProductSerializer, BranchSerializer, SupplierSerializer, InventorySerializer, InventoryAdjustSerializer
from accounts.permissions import IsAdminCliente, IsAdminClienteOrGerente
from core.models import Subscription # Para lógica de límites de plan


# ----------------------------------------------------
# Mixin para forzar el filtrado por Company (Tenancy)
# ----------------------------------------------------

class TenantModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet Base que asegura que todas las operaciones estén filtradas 
    por la compañía (tenant) del usuario autenticado.
    """
    permission_classes = [IsAuthenticated, IsAdminClienteOrGerente]
    
    def get_queryset(self):
        """
        Filtra el queryset para mostrar solo objetos de la compañía del usuario.
        """
        user = self.request.user
        
        if not user.is_authenticated or not user.is_active:
            return super().get_queryset().none()

        # Super Admin ve todos los objetos (si es necesario para gestión central)
        if user.role == 'super_admin':
             return super().get_queryset()
             
        # Admin Cliente/Gerente ven su tenant
        if user.company:
            return super().get_queryset().filter(company=user.company)
        
        return super().get_queryset().none()

    def perform_create(self, serializer):
        """
        Asigna automáticamente la compañía al nuevo objeto.
        """
        if not self.request.user.company:
            raise PermissionDenied("El usuario no está asociado a una compañía (tenant).")
            
        serializer.save(company=self.request.user.company)


# ----------------------------------------------------
# A. ViewSets CRUD (Rutas API)
# ----------------------------------------------------

class ProductViewSet(TenantModelViewSet):
    """
    CRUD de Productos (API). Listado público para e-commerce.
    Rutas: /api/products/
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def get_permissions(self):
        """Permitir listado (GET) público para e-commerce."""
        if self.action in ['list', 'retrieve']:
            # GET /api/products/ (público)
            return [AllowAny()]
        
        # POST, PUT/PATCH, DELETE requiere AdminCliente o Gerente
        return [IsAuthenticated(), IsAdminClienteOrGerente()]

class SupplierViewSet(TenantModelViewSet):
    """
    CRUD de Proveedores (API).
    Rutas: /api/suppliers/
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated, IsAdminClienteOrGerente]

class BranchViewSet(TenantModelViewSet):
    """
    CRUD de Sucursales (API). Solo para Admin Cliente.
    Rutas: /api/branches/
    """
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated, IsAdminCliente]
    
    def perform_create(self, serializer):
        """
        Valida el límite de sucursales según el plan de suscripción.
        """
        user = self.request.user
        
        try:
            subscription = Subscription.objects.get(company=user.company)
            current_count = Branch.objects.filter(company=user.company).count()

            if current_count >= subscription.max_branches:
                raise PermissionDenied(f"Límite de sucursales excedido ({subscription.max_branches}). Actualiza tu plan.")

            super().perform_create(serializer)
        except Subscription.DoesNotExist:
            raise PermissionDenied("La compañía no tiene un plan de suscripción válido.")

    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """
        GET /api/branches/{id}/inventory/ - Inventario por sucursal.
        """
        branch = self.get_object()
        
        if branch.company != request.user.company:
            raise PermissionDenied("No tienes permiso para ver el inventario de esta sucursal.")
            
        inventory = Inventory.objects.filter(branch=branch)
        serializer = InventorySerializer(inventory, many=True)
        return Response(serializer.data)


# ----------------------------------------------------
# B. Vistas de Inventario Específicas (API)
# ----------------------------------------------------

class InventoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Vistas específicas para listado filtrado y ajustes de inventario (API).
    Rutas: /api/inventory/, /api/inventory/adjust/
    """
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated, IsAdminClienteOrGerente]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['branch', 'product']

    def get_queryset(self):
        """Filtra el inventario por la compañía del usuario."""
        user = self.request.user
        if user.company:
            return Inventory.objects.filter(branch__company=user.company)
        return Inventory.objects.none()

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def adjust_stock(self, request):
        """
        POST /api/inventory/adjust/ - Ingreso/Salida manual de stock.
        """
        serializer = InventoryAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        branch_id = serializer.validated_data['branch_id']
        product_id = serializer.validated_data['product_id']
        adjustment = serializer.validated_data['adjustment_quantity']
        
        inventory_item = get_object_or_404(
            Inventory.objects.select_related('branch__company'), 
            branch_id=branch_id, 
            product_id=product_id
        )
        
        if inventory_item.branch.company != request.user.company:
            raise PermissionDenied("El producto o sucursal no pertenece a tu compañía.")

        # Actualizar stock
        Inventory.objects.filter(id=inventory_item.id).update(stock=F('stock') + adjustment)
        inventory_item.refresh_from_db()

        # Validación de Stock Negativo (si el stock es negativo por ajuste justificado, se permite)
        if inventory_item.stock < 0:
            # Puedes registrar un log de que un ajuste justificó el stock negativo
            pass 

        return Response({
            "detail": "Ajuste de inventario exitoso.",
            "new_stock": inventory_item.stock,
            "product": inventory_item.product.name
        }, status=status.HTTP_200_OK)