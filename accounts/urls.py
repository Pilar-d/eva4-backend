# accounts/urls.py

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path, include

# Importar las vistas DRF y las vistas de redirección/templates
# Asumiendo que user_create_template_view y login_success_redirect_view están ahora en .views
from .views import UserViewSet, login_success_redirect_view 
from .views_templates import user_create_template_view # Si aún mantienes esta estructura

# Define el namespace de la aplicación (usado en {% url 'accounts:...' %})
app_name = 'accounts'

# Configurar el Router (Genera rutas CRUD básicas como /api/users/, /api/users/{id}/)
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user') 

urlpatterns = [
    # ------------------------------------------------
    # 0. AUTH REDIRECTION VIEW (AÑADIDA)
    # ------------------------------------------------
    # Esta debe ser la URL a la que se redirige después del login exitoso, 
    # configurada en settings.LOGIN_REDIRECT_URL.
    path('redirect/', login_success_redirect_view, name='login_redirect'),
    
    # ------------------------------------------------
    # 1. TEMPLATE VIEWS (HTML Interface) - Definida para que gane la coincidencia GET
    # ------------------------------------------------
    
    # RUTA DE TEMPLATE (GET): Muestra el formulario HTML. 
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
    
    # Rutas CRUD DRF (e.g., GET /api/users/, /api/users/{id}/)
    path('', include(router.urls)), 
    
    # GET /api/users/me/
    path('users/me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
    
    # API PROCESS ROUTE (POST): El formulario HTML envía datos aquí.
    # POST /api/users/create/ (Endpoint explícito para el POST)
    path('api/users/create/', UserViewSet.as_view({'post': 'create'}), name='user_create_api'),
]