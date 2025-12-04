# sales/admin.py

from django.contrib import admin
from .models import Sale, SaleItem, Order, OrderItem, CartItem

# ----------------------------------------------------
# 1. Inlines (Detalles de la Transacción)
# ----------------------------------------------------

class SaleItemInline(admin.TabularInline):
    """Muestra los productos y cantidades dentro de una Venta POS."""
    model = SaleItem
    extra = 0 # No muestra filas vacías por defecto
    readonly_fields = ('product', 'quantity', 'price') # Se deben crear solo al registrar la venta
    fields = ('product', 'quantity', 'price')


class OrderItemInline(admin.TabularInline):
    """Muestra los productos y cantidades dentro de una Orden de E-commerce."""
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')
    fields = ('product', 'quantity', 'price')


# ----------------------------------------------------
# 2. Registros Principales
# ----------------------------------------------------

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    """Administración de Ventas Presenciales (POS)."""
    list_display = (
        'id', 
        'branch', 
        'user', 
        'total', 
        'payment_method', 
        'created_at'
    )
    list_filter = ('branch', 'payment_method', 'created_at')
    search_fields = ('user__username', 'branch__name', 'id')
    readonly_fields = ('total', 'created_at', 'branch', 'user')
    
    # Incluir los detalles de los productos
    inlines = [SaleItemInline]
    
    fieldsets = (
        (None, {'fields': ('branch', 'user', 'payment_method', 'total', 'created_at')}),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Administración de Órdenes de E-commerce."""
    list_display = (
        'id', 
        'company', 
        'cliente_final_name', 
        'estado', 
        'total', 
        'created_at'
    )
    list_filter = ('estado', 'company', 'created_at')
    search_fields = ('cliente_final_name', 'cliente_final_email', 'id')
    readonly_fields = ('total', 'created_at')
    
    # El campo 'estado' puede ser editable para que el Super Admin / Admin Cliente 
    # pueda cambiarlo (PENDIENTE -> ENVIADO -> ENTREGADO).
    list_editable = ('estado',) 

    # Incluir los detalles de los productos
    inlines = [OrderItemInline]

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Administración del Carrito de Compras Temporal (para usuarios logueados)."""
    list_display = ('user', 'product', 'quantity')
    list_filter = ('user',)
    search_fields = ('user__username', 'product__name')