# sales/shop_urls.py (MODIFICACIÓN)

from django.urls import path
from . import views_templates 

app_name = 'shop'

urlpatterns = [
    # ------------------------------------------------
    # 1. RUTAS DE E-COMMERCE (Shop)
    # ------------------------------------------------
    
    # ⚠️ CORRECCIÓN: RUTA RAÍZ (Home) ahora apunta a la vista de Solicitud de Planes
    path('', 
         views_templates.plan_request_view, # <-- Cambiado de catalogo_view
         name='home'), 

    # Catálogo (Lista de Productos)
    path('shop/products/', 
         views_templates.catalogo_view, 
         name='catalogo'), 
         
    # Detalle de Producto
    path('shop/products/<int:pk>/', 
         views_templates.detalle_producto_view, 
         name='detalle'),
         
    # Carrito de Compras
    path('shop/cart/', 
         views_templates.cart_view, 
         name='cart'),
         
    # Checkout
    path('shop/checkout/', 
         views_templates.checkout_view, 
         name='checkout'),

    # ------------------------------------------------
    # 2. RUTAS DE SOLICITUD DE CLIENTES (Public)
    # ------------------------------------------------
    
    # Vista de Plannes y Formulario de Solicitud (GET)
    path('request/plans/', 
         views_templates.plan_request_view, 
         name='plan_request'),
         
    # Procesamiento del Formulario de Solicitud (POST)
    path('request/submit/', 
         views_templates.submit_request, 
         name='request_submit'),
]