# accounts/urls.py

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path, include

# Vistas DRF
from .views import UserViewSet

# Vista Template (GET - crear usuario)
from .views_templates import user_create_template_view


# Namespace de la app
app_name = 'accounts'


# Router DRF
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')


urlpatterns = [
    # ------------------------------------------------
    # 1. TEMPLATE VIEW (HTML) – Formulario de creación
    # ------------------------------------------------
    path('users/create/', user_create_template_view, name='user_create'),

    # ------------------------------------------------
    # 2. JWT AUTH
    # ------------------------------------------------
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ------------------------------------------------
    # 3. USER API ENDPOINTS (DRF)
    # ------------------------------------------------
    path('', include(router.urls)),  # /users/ (GET, POST), /users/{id}/ etc

    path('users/me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),

    # POST desde el formulario HTML → DRF
    path('api/users/create/', UserViewSet.as_view({'post': 'create'}), name='user_create_api'),
]
