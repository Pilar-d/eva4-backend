# accounts/urls.py

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path, include
from .views import UserViewSet # Vistas DRF (para POST y API CRUD)
from .views_templates import user_create_template_view # Vistas Template (para GET/mostrar formulario)

# Define el namespace de la aplicación (usado en {% url 'accounts:...' %})
app_name = 'accounts'

# Configurar el Router (Genera rutas CRUD básicas como /api/users/, /api/users/{id}/)
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user') 

urlpatterns = [
    # ------------------------------------------------
    # 1. TEMPLATE VIEWS (HTML Interface) - Defined first for easy resolution
    # ------------------------------------------------
    
    # ⚠️ TEMPLATE GET ROUTE (GET): Muestra el formulario HTML. 
    # Este es el enlace que usa el dashboard: {% url 'accounts:user_create' %}
    path('users/create/', user_create_template_view, name='user_create'), 
    
    # ------------------------------------------------
    # 2. AUTHENTICATION (API JWT)
    # ------------------------------------------------
    # POST /api/token/
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # POST /api/token/refresh/
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ------------------------------------------------
    # 3. USER API ENDPOINTS (DRF)
    # ------------------------------------------------
    
    # Rutas CRUD DRF (e.g., GET /api/users/, POST /api/users/)
    path('', include(router.urls)), 
    
    # GET /api/users/me/
    path('users/me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
    
    # API PROCESS ROUTE (POST): El formulario HTML envía datos aquí.
    # POST /api/users/create/ (Endpoint explícito para el POST)
    path('api/users/create/', UserViewSet.as_view({'post': 'create'}), name='user_create_api'),
]