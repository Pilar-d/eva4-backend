# temucosoft_project/urls.py

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render 

def dashboard_view(request):
    """
    Ruta funcional del Dashboard. Redirige a login si no hay sesión.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    return render(request, 'dashboard.html', {'user': request.user})


urlpatterns = [
    # ------------------------------------------------
    # 1. APIs (prefijo /api/) 
    # ------------------------------------------------
    path('api/', include('accounts.urls')), 
    path('api/', include('core.urls')), 
    path('api/', include('products.urls')),
    path('api/', include('sales.urls')),

    # ------------------------------------------------
    # 2. Documentación Swagger [cite: 32, 253]
    # ------------------------------------------------
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # ------------------------------------------------
    # 3. Rutas de Sesión y Dashboard
    # ------------------------------------------------
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # ------------------------------------------------
    # 4. Vistas de E-commerce / Templates
    # ------------------------------------------------
    path('', include('sales.shop_urls')), 
]