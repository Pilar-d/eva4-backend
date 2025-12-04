# core/urls.py

from rest_framework.routers import DefaultRouter
from django.urls import path, include

# ⚠️ Importamos TODAS las vistas necesarias, incluyendo la vista de detalle de suscripción
from .views import (
    CompanyViewSet, 
    company_create_from_request_view, 
    company_list_template_view, 
    subscription_list_template_view,
    subscription_detail_view 
) 

app_name = 'core'

# 1. Configurar el Router para CompanyViewSet (Rutas API)
router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company-api') 

urlpatterns = [
    # -----------------------------------------------
    # 1. APIs (CRUD y Suscripción)
    # -----------------------------------------------
    
    # Rutas CRUD de DRF: /api/companies/ (GET, POST, etc.)
    path('', include(router.urls)), 
    
    # POST /api/companies/{id}/subscribe/ (Activación de plan)
    path('companies/<int:pk>/subscribe/', 
          CompanyViewSet.as_view({'post': 'subscribe'}), 
          name='company-subscribe-api'),
            
    # -----------------------------------------------
    # 2. Vistas de Templates (Super Admin Flow)
    # -----------------------------------------------
    
    # RUTA DE LISTADO DE COMPAÑÍAS (Template HTML)
    path('list/', company_list_template_view, name='company_list'), 
    
    # RUTA DE LISTADO DE SUSCRIPCIONES (Template HTML)
    path('subscriptions/', subscription_list_template_view, name='subscription_list'), 
    
    # ⚠️ FIX: RUTA DE DETALLE/EDICIÓN DE SUSCRIPCIÓN (Template HTML)
    path('subscriptions/<int:pk>/edit/', subscription_detail_view, name='subscription_detail'),
    
    # RUTA DE CREACIÓN DESDE SOLICITUD (Template HTML)
    path('company/create/from_request/<int:pk>/', 
          company_create_from_request_view, 
          name='company_create_from_request'),
]