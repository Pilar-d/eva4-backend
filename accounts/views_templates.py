# accounts/views_templates.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count

# Importar modelos y permisos locales
from core.models import Company 
from products.models import Branch # ⚠️ Necesario para obtener las sucursales
from accounts.models import User 
from accounts.permissions import is_super_admin_check, is_admin_cliente_check # Clases de chequeo

# ----------------------------------------------------
# VISTAS DE TEMPLATES (Creación de Usuarios)
# ----------------------------------------------------

def user_create_template_view(request):
    """
    Muestra el formulario HTML para crear nuevos usuarios.
    Define el contexto (roles, sucursales) basado en el rol del usuario autenticado.
    """
    user = request.user
    companies = None
    branches = []
    allowed_roles = []
    
    
    if not user.is_authenticated:
        # Caso: Usuario no autenticado (Debe ser redirigido al login/dashboard por el middleware)
        return redirect('login') 
        
    
    # Caso: USUARIO AUTENTICADO (Administración/Creación de Sub-usuarios)
    
    if user.role == 'super_admin':
        # Super Admin crea Admin Clients
        allowed_roles = [('admin_cliente', 'Admin Cliente (Tenant)')]
        companies = Company.objects.filter(is_active=True).order_by('name') # Necesita lista de tenants
        
    elif user.role == 'admin_cliente':
        # Admin Cliente crea Gerentes y Vendedores
        allowed_roles = [('gerente', 'Gerente'), ('vendedor', 'Vendedor')]
        
        # ⚠️ CRÍTICO: Obtener sucursales de la compañía actual
        if user.company:
            branches = Branch.objects.filter(company=user.company).values('id', 'name').order_by('name')
        
    else:
        # Si el usuario está logueado pero no tiene un rol para crear (ej: 'gerente' o 'vendedor'), redirigir
        messages.error(request, "Tu rol no te permite crear nuevos usuarios.")
        return redirect('dashboard')
            
    
    # --- Preparación del Contexto ---
    post_data = request.POST if request.method == 'POST' else {}

    context = {
        'user': user,
        'allowed_roles': allowed_roles,
        'companies': companies, # Lista de tenants (Super Admin)
        'branches': branches,   # ⚠️ Lista de sucursales (Admin Cliente)
        'post_data': post_data, # Retener datos en caso de error
    }
    
    return render(request, 'accounts/user_create.html', context)