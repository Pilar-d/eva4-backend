# sales/urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter 
from django.urls import include 

# Importamos las clases ViewSet de DRF (desde .views)
from .views import SaleViewSet, PurchaseViewSet, CartViewSet, ReportViewSet 
# Importamos las funciones de vistas de templates (desde .views_templates)
from .views_templates import (
    client_request_list_view, 
    request_delete_view, 
    pos_sale_view,
    purchase_create_template_view,
    sales_report_view # <-- Vista que renderiza sales/report_sales.html
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
    path('purchases/<int:pk>/create/', 
         purchase_create_template_view, 
         name='purchase_create'), 

    # 5. REPORTE DE VENTAS (HTML) - SOLUCIÓN AL REQUERIMIENTO
    path('reports/sales/', 
         sales_report_view, 
         name='report-sales'), 
    
    # ------------------------------------------------
    # B. API ENDPOINTS (DRF ViewSets)
    # ------------------------------------------------
    
    # 6. Ventas (POS) y Reportes de Ventas API 
    path('sales/', 
         SaleViewSet.as_view({'post': 'create', 'get': 'list'}), 
         name='sale-list-create'),

    # 7. Compras / Ingreso de Stock API 
    path('purchases/', 
         PurchaseViewSet.as_view({'post': 'create'}), 
         name='purchase-create-api'),

    # 8. Carrito / E-commerce API
    path('cart/add/', 
         CartViewSet.as_view({'post': 'add_item'}), 
         name='cart-add'),
         
    path('cart/checkout/', 
         CartViewSet.as_view({'post': 'checkout'}), 
         name='cart-checkout'),
         
    # 9. Reportes Mínimos API (JSON para Stock)
    path('reports/stock/', 
         ReportViewSet.as_view({'get': 'stock_report'}), 
         name='report-stock-api'), 
]