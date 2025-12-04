# accounts/views_templates.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test

# Importar modelos y permisos locales
from core.models import Company 
from accounts.permissions import is_super_admin_check, is_admin_cliente_check


@user_passes_test(is_super_admin_check or is_admin_cliente_check)
def user_create_template_view(request):
    """
    Muestra el formulario HTML para crear nuevos usuarios (Admin Cliente, Gerente, Vendedor).
    """
    user = request.user
    companies = None
    
    # 1. Define roles permitidos basados en quién crea
    if user.role == 'super_admin':
        # Super Admin crea Admin Clients
        allowed_roles = [('admin_cliente', 'Admin Cliente (Tenant)')]
        companies = Company.objects.filter(is_active=True) # Needs list of tenants
    elif user.role == 'admin_cliente':
        # Admin Cliente crea Gerentes y Vendedores
        allowed_roles = [('gerente', 'Gerente'), ('vendedor', 'Vendedor')]
    else:
        # Should be caught by the decorator
        return redirect('dashboard')
        
    context = {
        'user': user,
        'allowed_roles': allowed_roles,
        'companies': companies,
    }
    
    return render(request, 'accounts/user_create.html', context)