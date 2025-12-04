# products/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Importar las vistas de la API (ViewSets)
from .views import (
    ProductViewSet, 
    BranchViewSet, # Importado para el Router
    SupplierViewSet,
    InventoryViewSet,
)

# Importar las vistas basadas en Templates
from .views_templates import (
    product_list_view, product_create_view, product_update_view, product_detail_view,
    supplier_list_view, supplier_create_view, supplier_update_view,
    branch_list_view, branch_create_view, branch_update_view, # <-- Vista de Template
    inventory_list_view,
)

app_name = 'products'
# =========================================================
# 1. Rutas de la API (DRF Router)
# =========================================================
router = DefaultRouter()
# El basename se usa para generar los nombres de las URLs de la API (ej: branch-api-list)
router.register(r'branches', BranchViewSet, basename='branch-api') 
router.register(r'products', ProductViewSet, basename='product-api')
router.register(r'suppliers', SupplierViewSet, basename='supplier-api')
router.register(r'inventory', InventoryViewSet, basename='inventory-api')


# =========================================================
# 2. Rutas de TEMPLATES HTML (PRIORIDAD MÁXIMA)
# =========================================================
# ESTA LISTA DEBE SER LA PRIMERA EN urlpatterns.
urlpatterns_templates = [

    path('inventory/', 
     InventoryViewSet.as_view({'get': 'list'}), 
     name='inventory-list-api'),
    # Sucursales (FIX: Esta ruta DEBE ganar la coincidencia)
    path('branches/list/', branch_list_view, name='branch_list'),
    path('branches/create/', branch_create_view, name='branch_create'),
    path('branches/<int:pk>/update/', branch_update_view, name='branch_update'),

    # Productos
    path('products/list/', product_list_view, name='product_list'),
    path('products/create/', product_create_view, name='product_create'),
    path('products/<int:pk>/', product_detail_view, name='product_detail'),
    path('products/<int:pk>/update/', product_update_view, name='product_update'),

    # Proveedores
    path('suppliers/list/', supplier_list_view, name='supplier_list'),
    path('suppliers/create/', supplier_create_view, name='supplier_create'),
    path('suppliers/<int:pk>/update/', supplier_update_view, name='supplier_update'),
    
    # Inventario
    path('inventory/list/', inventory_list_view, name='inventory_list'),
]


# =========================================================
# 3. Concatenación Final de URLS
# =========================================================
# Se combinan ambas listas, TEMPLATES primero, para asegurar la prioridad.
urlpatterns = urlpatterns_templates + [
    # Incluir todas las URLs del router
    path('', include(router.urls)),
]