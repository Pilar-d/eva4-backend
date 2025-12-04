# accounts/views.py

from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError

# Django imports for template views
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test

# Importar modelos, serializadores y permisos locales
from .models import User
from .serializers import UserSerializer
from .permissions import IsSuperAdmin, IsAdminCliente, is_super_admin_check, is_admin_cliente_check # Import all necessary checks/classes
from core.models import Company # Necessary for querying companies


# ----------------------------------------------------
# 1. TEMPLATE VIEW (GET): Renders the HTML Form
# ----------------------------------------------------

# Note: The combined check is defined in accounts/permissions.py
@user_passes_test(is_super_admin_check or is_admin_cliente_check)
def user_create_template_view(request):
    """
    Renders the HTML form for creating new users.
    This is the view linked from the dashboard/menu.
    """
    user = request.user
    companies = None
    
    # 1. Define roles allowed based on creator
    if user.role == 'super_admin':
        # Super Admin creates Admin Clients
        allowed_roles = [('admin_cliente', 'Admin Cliente (Tenant)')]
        companies = Company.objects.filter(is_active=True) # Needs list of tenants
    elif user.role == 'admin_cliente':
        # Admin Cliente creates Gerentes and Vendedores
        allowed_roles = [('gerente', 'Gerente'), ('vendedor', 'Vendedor')]
    else:
        # Should be caught by the decorator, but a safe fallback
        return redirect('dashboard')
        
    context = {
        'user': user,
        'allowed_roles': allowed_roles,
        'companies': companies,
        # Errors from a previous failed API POST can be retrieved from session/messages if needed
    }
    
    return render(request, 'accounts/user_create.html', context)


# ----------------------------------------------------
# 2. API VIEWSET (DRF): Handles POST /api/users/create/ and GET /api/users/me/
# ----------------------------------------------------

class UserViewSet(mixins.CreateModelMixin, 
                  mixins.RetrieveModelMixin, 
                  mixins.UpdateModelMixin, 
                  viewsets.GenericViewSet):
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_queryset(self):
        """Filters queryset based on user role (Tenancy)."""
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
            
        if user.role == 'super_admin':
            return User.objects.all()
            
        if user.role in ['admin_cliente', 'gerente'] and user.company:
            return User.objects.filter(company=user.company)
            
        return User.objects.filter(id=user.id)

    def get_permissions(self):
        """Assigns permissions based on action."""
        if self.action == 'create':
            # POST /api/users/create/ requires SuperAdmin OR AdminCliente
            return [IsAuthenticated(), IsSuperAdmin() | IsAdminCliente()]
        
        # For 'me' and other retrieves
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """
        Handles user creation and enforces role/tenancy rules.
        """
        creator = self.request.user
        data = self.request.data
        role_to_create = data.get('role')
        company_id_data = data.get('company') 

        # 1. IS_ACTIVE Check
        if not creator.is_active:
            raise PermissionDenied("Tu cuenta está inactiva y no puedes realizar esta acción.")

        # 2. Control of Roles and Tenancy 
        if creator.role == 'super_admin':
            if role_to_create != 'admin_cliente':
                 raise ValidationError({"role": "Super Admin solo puede crear 'admin_cliente' y configurar cuentas base."})
                 
            if not company_id_data:
                raise ValidationError({"company": "Super Admin debe especificar la compañía (tenant) a asignar."})
                
            # Assign company ID passed in data
            serializer.save(is_active=True, company_id=company_id_data)
            
        elif creator.role == 'admin_cliente':
            if role_to_create not in ['gerente', 'vendedor']:
                raise PermissionDenied(f"Admin Cliente no puede crear el rol: {role_to_create}.")

            # Force company to be the creator's company
            serializer.save(is_active=True, company=creator.company)
        
        else:
             raise PermissionDenied("Solo el Super Admin o el Admin Cliente pueden crear nuevos usuarios.")

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        GET /api/users/me/ - Get authenticated user info.
        """
        user = request.user
        
        if not user.is_active:
             return Response({"detail": "Cuenta inactiva."}, status=status.HTTP_403_FORBIDDEN)
             
        serializer = self.get_serializer(user)
        return Response(serializer.data)