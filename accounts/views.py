# accounts/views.py

from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings  # Para LOGIN_REDIRECT_URL

from .models import User
from .serializers import UserSerializer
from .permissions import (
    IsSuperAdmin, IsAdminCliente,
    is_super_admin_check, is_admin_cliente_check, CustomOr
)
from core.models import Company


# ----------------------------------------------------
# 0. VIEW PARA MANEJAR REDIRECCIÓN POST-LOGIN
# ----------------------------------------------------
def login_success_redirect_view(request):
    user = request.user
    next_url = request.GET.get('next')

    if next_url == '/api/users/create/':
        if is_super_admin_check(user) or is_admin_cliente_check(user):
            return user_create_template_view(request)
        else:
            return redirect(settings.LOGIN_REDIRECT_URL)

    return redirect(next_url or settings.LOGIN_REDIRECT_URL)


# ----------------------------------------------------
# 1. TEMPLATE VIEW (GET): Renders the HTML Form
# ----------------------------------------------------
@user_passes_test(lambda u: is_super_admin_check(u) or is_admin_cliente_check(u))
def user_create_template_view(request):
    user = request.user
    companies = None
    branches = []

    if user.role == 'super_admin':
        allowed_roles = [('admin_cliente', 'Admin Cliente (Tenant)')]
        companies = Company.objects.filter(is_active=True).order_by('name')

    elif user.role == 'admin_cliente':
        allowed_roles = [('gerente', 'Gerente'), ('vendedor', 'Vendedor')]
        if user.company:
            from products.models import Branch
            branches = Branch.objects.filter(company=user.company).order_by('name')
    else:
        return redirect('dashboard')

    post_data = request.POST if request.method == 'POST' else {}

    context = {
        'user': user,
        'allowed_roles': allowed_roles,
        'companies': companies,
        'branches': branches,
        'post_data': post_data,
    }

    return render(request, 'accounts/user_create.html', context)


# ----------------------------------------------------
# 2. API VIEWSET (DRF)
# ----------------------------------------------------
class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        if user.role == 'super_admin':
            return User.objects.all()
        if user.role in ['admin_cliente', 'gerente'] and user.company:
            return User.objects.filter(company=user.company)
        return User.objects.filter(id=user.id)

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), CustomOr(IsSuperAdmin(), IsAdminCliente())]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """
        Sobrescribimos create() para redirigir al dashboard después de crear usuario.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Redirigir al dashboard después de crear usuario (HTML form POST)
        if request.content_type == 'application/x-www-form-urlencoded':
            return redirect(settings.LOGIN_REDIRECT_URL)

        # Para llamadas API normales, devolver datos de usuario creado
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        creator = self.request.user
        data = self.request.data
        role_to_create = data.get('role')
        company_id_data = data.get('company')
        branch_id_data = data.get('branch')  # Nuevo campo branch

        if not creator.is_active:
            raise PermissionDenied("Tu cuenta está inactiva y no puedes realizar esta acción.")

        # ------------------- SUPER ADMIN -------------------
        if creator.role == 'super_admin':
            if role_to_create != 'admin_cliente':
                raise ValidationError({"role": "Super Admin solo puede crear 'admin_cliente'."})
            if not company_id_data:
                raise ValidationError({"company": "Super Admin debe asignar la compañía (tenant)."})
            serializer.save(is_active=True, company_id=company_id_data)

        # ------------------- ADMIN CLIENTE -------------------
        elif creator.role == 'admin_cliente':
            if role_to_create not in ['gerente', 'vendedor']:
                raise PermissionDenied(f"Admin Cliente no puede crear el rol: {role_to_create}.")
            if not branch_id_data:
                raise ValidationError({"branch": "Debe seleccionar una sucursal para Gerente o Vendedor."})

            serializer.save(is_active=True, company=creator.company, branch_id=branch_id_data)

        else:
            raise PermissionDenied("Solo Super Admin o Admin Cliente pueden crear usuarios.")

    @action(detail=False, methods=['get'])
    def me(self, request):
        user = request.user
        if not user.is_active:
            return Response({"detail": "Cuenta inactiva."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(user)
        return Response(serializer.data)
