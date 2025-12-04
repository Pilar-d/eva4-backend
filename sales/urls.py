# sales/urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter # Included for completeness
from django.urls import include 

# Importamos las clases ViewSet de DRF (desde .views)
from .views import SaleViewSet, PurchaseViewSet, CartViewSet, ReportViewSet 
# Importamos las funciones de vistas de templates (desde .views_templates)
from .views_templates import (
    client_request_list_view, 
    request_delete_view, 
    pos_sale_view,
    purchase_create_template_view # <-- Vista para el formulario GET
)

# Definimos el namespace 'sales' para ser usado en {% url 'sales:...' %}
app_name = 'sales' 

urlpatterns = [
    # ------------------------------------------------
    # A. VISTAS DE TEMPLATES (HTML)
    # ------------------------------------------------
    
    # 1. Punto de Venta (POS) - Vendedor
    path('pos/sale/', 
         pos_sale_view, 
         name='pos_sale'), 
    
    # 2. Listado de Solicitudes - Super Admin
    path('requests/', 
         client_request_list_view, 
         name='request-list'),
         
    # 3. Eliminar Solicitud - Super Admin (POST)
    path('requests/<int:pk>/delete/', 
         request_delete_view, 
         name='request_delete'),
         
    # 4. Creación de Compra/Ingreso de Stock - Template (GET)
    # Ejemplo: /purchases/1/create/ (Muestra el formulario para el proveedor ID 1)
    path('purchases/<int:pk>/create/', 
         purchase_create_template_view, 
         name='purchase_create'), # <-- Usado por el template products/supplier_list.html

    # ------------------------------------------------
    # B. API ENDPOINTS (DRF ViewSets)
    # ------------------------------------------------
    
    # 5. Ventas (POS) y Reportes de Ventas API
    path('sales/', 
         SaleViewSet.as_view({'post': 'create', 'get': 'list'}), 
         name='sale-list-create'),

    # 6. Compras / Ingreso de Stock API (POST para procesar el formulario)
    # Rutas: /api/purchases/ (API de procesamiento, renombrada a -api)
    path('purchases/', 
         PurchaseViewSet.as_view({'post': 'create'}), 
         name='purchase-create-api'),

    # 7. Carrito / E-commerce API
    path('cart/add/', 
         CartViewSet.as_view({'post': 'add_item'}), 
         name='cart-add'),
         
    path('cart/checkout/', 
         CartViewSet.as_view({'post': 'checkout'}), 
         name='cart-checkout'),
         
    # 8. Reportes Mínimos API
    path('reports/stock/', 
         ReportViewSet.as_view({'get': 'stock_report'}), 
         name='report-stock'),
         
    path('reports/sales/', 
         ReportViewSet.as_view({'get': 'sales_report'}), 
         name='report-sales'),
]