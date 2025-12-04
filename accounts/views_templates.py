# accounts/views_templates.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test

# Importar modelos y permisos locales
from core.models import Company 
from products.models import Branch 
from accounts.permissions import is_super_admin_check, is_admin_cliente_check 


# ----------------------------------------------------
# VISTA TEMPLATE PARA CREACIÓN DE USUARIOS
# ----------------------------------------------------
@user_passes_test(lambda u: is_super_admin_check(u) or is_admin_cliente_check(u))
def user_create_template_view(request):
    """
    Muestra el formulario HTML para crear un usuario según el rol del creador.
    - Super Admin -> crea Admin Cliente (tenant admins)
    - Admin Cliente -> crea Gerentes y Vendedores
    """
    user = request.user
    companies = None
    branches = []
    allowed_roles = []

    # -----------------------------
    # CASO SUPER ADMIN
    # -----------------------------
    if user.role == 'super_admin':
        allowed_roles = [
            ('admin_cliente', 'Admin Cliente (Tenant)')
        ]
        companies = Company.objects.filter(is_active=True).order_by('name')

    # -----------------------------
    # CASO ADMIN CLIENTE
    # -----------------------------
    elif user.role == 'admin_cliente':
        allowed_roles = [
            ('gerente', 'Gerente'),
            ('vendedor', 'Vendedor'),
        ]

        # Validación extra: admin cliente debe tener compañía asignada
        if not user.company:
            messages.error(request, "Tu usuario no está asociado a ninguna compañía.")
            return redirect('dashboard')

        branches = Branch.objects.filter(company=user.company).order_by('name')

    # -----------------------------
    # CASO NO AUTORIZADO
    # -----------------------------
    else:
        messages.error(request, "Tu rol no te permite crear nuevos usuarios.")
        return redirect('dashboard')

    # -----------------------------
    # Preparar contexto
    # -----------------------------
    post_data = request.POST if request.method == 'POST' else {}

    context = {
        'user': user,
        'allowed_roles': allowed_roles,
        'companies': companies,
        'branches': branches,
        'post_data': post_data,
    }

    return render(request, 'accounts/user_create.html', context)
