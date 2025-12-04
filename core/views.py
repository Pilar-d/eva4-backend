# core/views.py

from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from rest_framework.exceptions import PermissionDenied 
from django.db.models import Count, F 
from django.utils.crypto import get_random_string 

# Importar modelos, serializadores y permisos locales
from .models import Company, Subscription
from .serializers import CompanySerializer, SubscriptionActionSerializer
from accounts.permissions import IsSuperAdmin # Clase de permiso para ViewSet
from accounts.models import User
from sales.models import ClientRequest 
from accounts.utils import validar_rut 

# ----------------------------------------------------
# Funciones de Soporte
# ----------------------------------------------------

def is_super_admin_check(user):
    """Verifica si el usuario es super_admin y activo (para @user_passes_test)."""
    # [cite_start]El requisito exige verificar is_active antes de permitir el acceso [cite: 95]
    return user.is_authenticated and user.is_active and user.role == 'super_admin'

# ----------------------------------------------------
# 1. CompanyViewSet (API DRF)
# ----------------------------------------------------

class CompanyViewSet(mixins.CreateModelMixin, 
                     mixins.ListModelMixin,   
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    
    def get_permissions(self):
        """Restringe todas las operaciones CRUD de Company solo al Super Admin."""
        if self.action in ['create', 'list', 'retrieve', 'subscribe']:
            return [IsAuthenticated(), IsSuperAdmin()]
        
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def subscribe(self, request, pk=None):
        """POST /api/companies/{id}/subscribe/ - Activa o modifica un plan de suscripción."""
        company = self.get_object()
        serializer = SubscriptionActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_name = serializer.validated_data['plan_name']

        subscription, created = Subscription.objects.get_or_create(company=company)

        subscription.plan_name = plan_name
        subscription.active = True 
        
        # [cite_start]Lógica para setear restricciones (según requisito [cite: 46])
        if plan_name == 'BASICO':
            subscription.max_branches = 3
        elif plan_name == 'ESTANDAR':
            subscription.max_branches = 6
        elif plan_name == 'PREMIUM':
            subscription.max_branches = 9
            
        subscription.save() 

        return Response({"detail": f"Plan {plan_name} activado para {company.name}."}, status=status.HTTP_200_OK)


# ----------------------------------------------------
# 2. Vistas de Templates (Flujo de Creación desde Solicitud)
# ----------------------------------------------------

@user_passes_test(is_super_admin_check)
def company_create_from_request_view(request, pk):
    """
    GET: Muestra formulario para crear Company y Admin Cliente basado en ClientRequest.
    POST: Procesa la creación del Tenant y el Admin Cliente.
    """
    client_request = get_object_or_404(ClientRequest, pk=pk, status='PENDIENTE')
    
    # Pre-llenado de datos (para GET)
    initial_data = {
        'company_name': client_request.company_name,
        'rut': client_request.rut,
        'plan_name': client_request.plan_name,
        'admin_email': client_request.contact_email,
    }

    if request.method == 'POST':
        # ⚠️ CAPTURA POST DATA
        post_data = {
            'company_name': request.POST.get('company_name'), 'admin_username': request.POST.get('admin_username'),
            'admin_rut': request.POST.get('admin_rut'), 'admin_email': request.POST.get('admin_email'),
            'plan_name': client_request.plan_name, 'rut': client_request.rut, 
        }
        
        company_name = post_data['company_name']; admin_username = post_data['admin_username']
        admin_rut = post_data['admin_rut']; admin_email = post_data['admin_email']
        
        # Validación de campos requeridos
        if not all([company_name, admin_username, admin_rut, admin_email]):
            messages.error(request, "Faltan datos esenciales para crear la Compañía o el Admin Cliente.")
            return render(request, 'core/company_form_from_request.html', {'request_data': client_request, 'initial': post_data})


        if not validar_rut(admin_rut):
            messages.error(request, "El RUT del Administrador Cliente no es válido.")
            return render(request, 'core/company_form_from_request.html', {'request_data': client_request, 'initial': post_data})

        
        # 🛑 Verificar la unicidad del RUT de la Compañía antes de la creación
        rut_compania = client_request.rut
        if Company.objects.filter(rut=rut_compania).exists():
            messages.error(request, f"Error (Duplicado): Ya existe una cuenta de cliente con el RUT de compañía {rut_compania}. No se puede crear un duplicado.")
            return render(request, 'core/company_form_from_request.html', {'request_data': client_request, 'initial': post_data})


        try:
            with transaction.atomic():
                # 1. Crear Company (Tenant)
                new_company = Company.objects.create(name=company_name, rut=rut_compania, is_active=True)
                
                # 2. Asignar el Plan (Subscription)
                subscription, created = Subscription.objects.get_or_create(company=new_company)
                subscription.plan_name = client_request.plan_name; subscription.active = True
                if client_request.plan_name == 'BASICO': subscription.max_branches = 3
                elif client_request.plan_name == 'ESTANDAR': subscription.max_branches = 6
                elif client_request.plan_name == 'PREMIUM': subscription.max_branches = 9
                subscription.save()
                
                # 3. Crear el Admin Cliente (User) - FIX: Generación segura de contraseña
                temp_password = get_random_string(12) 
                admin_user = User.objects.create_user(
                    username=admin_username, email=admin_email, password=temp_password, rut=admin_rut, 
                    role='admin_cliente', company=new_company, is_active=True
                )
                
                # 4. Marcar la petición como ACEPTADA
                client_request.status = 'ACEPTADO'
                client_request.save()
                
            messages.success(request, f"Cuenta '{new_company.name}' creada. Admin: {admin_user.username}. Password temporal: {temp_password}. Envía credenciales.")
            return redirect('core:company_list') 

        except Exception as e:
            messages.error(request, f"Error al crear la cuenta: {e}")
            return render(request, 'core/company_form_from_request.html', {'request_data': client_request, 'initial': post_data})

    
    # GET Request: Mostrar el formulario pre-rellenado
    return render(request, 'core/company_form_from_request.html', {'request_data': client_request, 'initial': initial_data})

# ----------------------------------------------------
# 3. Vista de Listado de Solicitudes (para Admin)
# ----------------------------------------------------

@user_passes_test(is_super_admin_check)
def client_request_list_view(request):
    """
    Muestra la lista de solicitudes PENDIENTES de clientes.
    """
    pending_requests = ClientRequest.objects.filter(status='PENDIENTE').order_by('-created_at')
    
    return render(request, 'sales/request_admin_list.html', {'pending_requests': pending_requests})


# ----------------------------------------------------
# 4. Vistas de Listado de Templates (para Super Admin - HTML)
# ----------------------------------------------------

@user_passes_test(is_super_admin_check)
def company_list_template_view(request):
    """Muestra el listado de todas las compañías en un template HTML."""
    companies = Company.objects.all().select_related('subscription').order_by('name')
    return render(request, 'core/company_list.html', {'companies': companies})


@user_passes_test(is_super_admin_check)
def subscription_list_template_view(request):
    """Muestra el listado de suscripciones para revisión del Super Admin."""
    companies = Company.objects.all().select_related('subscription').order_by('name')
    return render(request, 'core/subscription_list.html', {'companies': companies})


@user_passes_test(is_super_admin_check)
def subscription_detail_view(request, pk):
    """
    GET: Muestra la gestión de suscripción para una compañía específica (edición de plan).
    POST: Procesa el cambio de plan/restricciones (utilizando la lógica de la API subscribe o similar).
    """
    from .models import Subscription # Asegurar importación local
    
    # Usamos select_related para obtener la suscripción en una sola consulta
    company = get_object_or_404(Company.objects.select_related('subscription'), pk=pk)
    
    # Pre-cargar datos del plan actual
    current_plan = company.subscription.plan_name if hasattr(company, 'subscription') else None
    
    if request.method == 'POST':
        plan_name = request.POST.get('plan_name')
        
        # Lógica de procesamiento:
        if plan_name in dict(Subscription.PLAN_CHOICES):
            
            company.subscription.plan_name = plan_name
            company.subscription.active = True
            company.subscription.save() # Esto dispara el cálculo de max_branches y end_date
            messages.success(request, f"Plan de {company.name} actualizado a {plan_name}.")
            return redirect('core:company_list')
        else:
            messages.error(request, "Plan inválido.")
            return redirect('core:subscription_detail', pk=pk) 

    # GET: Preparar contexto para renderizar el formulario
    context = {
        'company': company,
        'plan_choices': Subscription.PLAN_CHOICES, # Pasa la lista de opciones
        'current_plan_code': current_plan,
    }
    
    # Renderiza el template que espera el objeto 'company'
    return render(request, 'core/subscription_list.html', context)


# core/views.py

from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from rest_framework.exceptions import PermissionDenied 
from django.db.models import Count, F 
from django.utils.crypto import get_random_string 

# Importar modelos, serializadores y permisos locales
from .models import Company, Subscription
from .serializers import CompanySerializer, SubscriptionActionSerializer
from accounts.permissions import IsSuperAdmin 
from accounts.models import User
from sales.models import ClientRequest 
from accounts.utils import validar_rut 

def is_super_admin_check(user):
    """Verifica si el usuario es super_admin y activo (para @user_passes_test)."""
    return user.is_authenticated and user.is_active and user.role == 'super_admin'

# ... (CompanyViewSet y otras funciones API) ...

@user_passes_test(is_super_admin_check)
def company_create_from_request_view(request, pk):
    """Flujo de creación de cuenta y admin cliente."""
    client_request = get_object_or_404(ClientRequest, pk=pk, status='PENDIENTE')
    initial_data = {'company_name': client_request.company_name, 'rut': client_request.rut,
                    'plan_name': client_request.plan_name, 'admin_email': client_request.contact_email}

    if request.method == 'POST':
        post_data = {'company_name': request.POST.get('company_name'), 'admin_username': request.POST.get('admin_username'),
                     'admin_rut': request.POST.get('admin_rut'), 'admin_email': request.POST.get('admin_email'),
                     'plan_name': client_request.plan_name, 'rut': client_request.rut}
        
        company_name = post_data['company_name']; admin_username = post_data['admin_username']
        admin_rut = post_data['admin_rut']; admin_email = post_data['admin_email']
        
        if not all([company_name, admin_username, admin_rut, admin_email]):
            messages.error(request, "Faltan datos esenciales para crear la Compañía o el Admin Cliente.")
            return render(request, 'core/company_form_from_request.html', {'request_data': client_request, 'initial': post_data})

        if not validar_rut(admin_rut):
            messages.error(request, "El RUT del Administrador Cliente no es válido.")
            return render(request, 'core/company_form_from_request.html', {'request_data': client_request, 'initial': post_data})

        # FIX: Verificar la unicidad del RUT de la Compañía antes de la creación
        rut_compania = client_request.rut
        if Company.objects.filter(rut=rut_compania).exists():
            messages.error(request, f"Error (Duplicado): Ya existe una cuenta de cliente con el RUT de compañía {rut_compania}. No se puede crear un duplicado.")
            return render(request, 'core/company_form_from_request.html', {'request_data': client_request, 'initial': post_data})

        try:
            with transaction.atomic():
                new_company = Company.objects.create(name=company_name, rut=rut_compania, is_active=True)
                subscription, _ = Subscription.objects.get_or_create(company=new_company)
                subscription.plan_name = client_request.plan_name; subscription.active = True
                if client_request.plan_name == 'BASICO': subscription.max_branches = 3
                elif client_request.plan_name == 'ESTANDAR': subscription.max_branches = 6
                elif client_request.plan_name == 'PREMIUM': subscription.max_branches = 9
                subscription.save()
                
                # FIX: Generación segura de contraseña
                temp_password = get_random_string(12) 
                admin_user = User.objects.create_user(
                    username=admin_username, email=admin_email, password=temp_password, rut=admin_rut, 
                    role='admin_cliente', company=new_company, is_active=True
                )
                
                client_request.status = 'ACEPTADO'; client_request.save()
                
            messages.success(request, f"Cuenta creada. Admin: {admin_user.username}. Password temporal: {temp_password}. Envía credenciales.")
            return redirect('core:company_list') 
        except Exception as e:
            messages.error(request, f"Error al crear la cuenta: {e}")
            return render(request, 'core/company_form_from_request.html', {'request_data': client_request, 'initial': post_data})
    
    return render(request, 'core/company_form_from_request.html', {'request_data': client_request, 'initial': initial_data})