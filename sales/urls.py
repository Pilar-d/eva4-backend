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
    pos_sale_view
)

# Definimos el namespace 'sales' para ser usado en {% url 'sales:...' %}
app_name = 'sales' 

urlpatterns = [
    # ------------------------------------------------
    # A. VISTAS DE TEMPLATES (HTML, para Vendedor y Super Admin)
    # ------------------------------------------------
    
    # 1. Punto de Venta (POS) - Vendedor
    path('pos/sale/', 
         pos_sale_view, 
         name='pos_sale'), 
    
    # 2. Listado de Solicitudes - Super Admin (GET)
    path('requests/', 
         client_request_list_view, 
         name='request-list'),
         
    # 3. Eliminar Solicitud - Super Admin (POST)
    path('requests/<int:pk>/delete/', 
         request_delete_view, 
         name='request_delete'),
         
    # ------------------------------------------------
    # B. API ENDPOINTS (DRF ViewSets)
    # ------------------------------------------------
    
    # 4. Ventas (POS) y Reportes de Ventas API
    path('sales/', 
         SaleViewSet.as_view({'post': 'create', 'get': 'list'}), 
         name='sale-list-create'),

    # 5. Compras / Ingreso de Stock API
    path('purchases/', 
         PurchaseViewSet.as_view({'post': 'create'}), 
         name='purchase-create'),

    # 6. Carrito / E-commerce API
    path('cart/add/', 
         CartViewSet.as_view({'post': 'add_item'}), 
         name='cart-add'),
         
    path('cart/checkout/', 
         CartViewSet.as_view({'post': 'checkout'}), 
         name='cart-checkout'),
         
    # 7. Reportes Mínimos API
    path('reports/stock/', 
         ReportViewSet.as_view({'get': 'stock_report'}), 
         name='report-stock'),
         
    path('reports/sales/', 
         ReportViewSet.as_view({'get': 'sales_report'}), 
         name='report-sales'),
]