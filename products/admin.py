# products/admin.py

from django.contrib import admin
from .models import Product, Branch, Supplier, Inventory

# ----------------------------------------------------
# 1. Inline para la relación Branch x Product (Inventory)
# ----------------------------------------------------

class InventoryInline(admin.TabularInline):
    """
    Permite gestionar los niveles de stock (Inventory) directamente
    desde la página de edición de la Sucursal (Branch).
    """
    model = Inventory
    extra = 1 # Muestra una fila vacía para añadir un nuevo producto/stock
    fields = ('product', 'stock', 'reorder_point') 
    list_display = fields


# ----------------------------------------------------
# 2. Registros Principales
# ----------------------------------------------------

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Administración del modelo Product."""
    list_display = (
        'sku', 
        'name', 
        'category', 
        'price', 
        'cost', 
        'company'
    )
    list_filter = ('company', 'category')
    search_fields = ('name', 'sku', 'description')
    readonly_fields = ('company',) # Generalmente la compañía se asigna en la vista/serializer
    
    fieldsets = (
        (None, {'fields': ('name', 'sku', 'description', 'category', 'company')}),
        ('Precios', {'fields': ('price', 'cost')}),
    )

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    """Administración de las Sucursales."""
    list_display = ('name', 'company', 'address', 'phone')
    list_filter = ('company',)
    search_fields = ('name', 'address')
    readonly_fields = ('company',)
    
    # Incluir el inline de Inventario
    inlines = [InventoryInline]

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Administración de los Proveedores."""
    list_display = ('name', 'rut', 'contact', 'company')
    list_filter = ('company',)
    search_fields = ('name', 'rut')
    readonly_fields = ('company',)
    
    fieldsets = (
        (None, {'fields': ('name', 'rut', 'contact', 'company')}),
    )

# ----------------------------------------------------
# 3. Registro del Modelo de Inventario (Opcional, para gestión directa)
# ----------------------------------------------------

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    """
    Administración directa de las relaciones Stock/Sucursal/Producto.
    Útil para ajustes masivos de stock.
    """
    list_display = ('product', 'branch', 'stock', 'reorder_point')
    list_filter = ('branch__company', 'branch', 'product__category')
    search_fields = ('product__name', 'branch__name')
    list_editable = ('stock', 'reorder_point') # Permite editar el stock directamente en la lista