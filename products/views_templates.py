# products/views_templates.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.forms import model_to_dict
from django.db.models import F
from django.urls import reverse
from django.http import HttpResponse

# Importar modelos y serializadores
from .models import Product, Branch, Supplier, Inventory
from .serializers import ProductSerializer, SupplierSerializer, BranchSerializer 
from core.models import Subscription 
# Importamos checks funcionales
from accounts.permissions import is_admin_cliente_or_gerente_check, is_admin_cliente_check
from accounts.utils import validar_rut 

# ----------------------------------------------------
# Vistas Auxiliares (Redirects to Dashboard if no Company)
# ----------------------------------------------------

def check_company(user, request):
    """Verifica la autenticación y la asociación de compañía (tenancy)."""
    if not user.company:
        messages.error(request, "Usuario no asociado a una compañía.")
        return redirect('dashboard')
    return None

# ----------------------------------------------------
# 1. PRODUCTOS (Admin Cliente / Gerente)
# ----------------------------------------------------

@user_passes_test(is_admin_cliente_or_gerente_check)
def product_list_view(request):
    """Muestra el listado de productos de la compañía (HTML)."""
    if response := check_company(request.user, request):
        return response
        
    products = Product.objects.filter(company=request.user.company).order_by('name')
    return render(request, 'products/product_list.html', {'products': products})


@user_passes_test(is_admin_cliente_or_gerente_check)
def product_create_view(request):
    """Muestra y procesa el formulario de creación de producto (POST tradicional)."""
    if response := check_company(request.user, request):
        return response
    
    user = request.user
    
    # ⚠️ FIX: Definimos el contexto base y opciones de categoría
    context = {
        'user': user, 
        'product': None, 
        'category_choices': Product.CATEGORY_CHOICES # CRÍTICO: Pasa las opciones de categoría
    } 
    
    if request.method == 'POST':
        data = request.POST.copy()
        serializer = ProductSerializer(data=data)
        
        if serializer.is_valid():
            try:
                serializer.save(company=user.company)
                messages.success(request, f"Producto '{data['name']}' creado con éxito.")
                return redirect('products:product_list')
            except Exception as e:
                messages.error(request, f"Error al guardar: {e}")
        else:
            for field, errors in serializer.errors.items():
                messages.error(request, f"Error en {field}: {', '.join(errors)}")
            
            context['post_data'] = request.POST # Pasa datos POST para repoblar el formulario
            # El contexto ya contiene 'product': None y las 'category_choices'
            return render(request, 'products/product_form.html', context)
            
    # GET Request: Initial Load
    context['post_data'] = {} # Inicializa 'post_data' como diccionario vacío en GET
    return render(request, 'products/product_form.html', context)


@user_passes_test(is_admin_cliente_or_gerente_check)
def product_detail_view(request, pk):
    """Muestra el detalle del producto y su inventario por sucursal."""
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    
    inventory_data = Inventory.objects.filter(product=product).select_related('branch').values(
        'stock', 'reorder_point', 'branch__name'
    ).annotate(branch_name=F('branch__name'))

    context = {
        'product': product,
        'inventory_data': inventory_data
    }
    return render(request, 'products/product_detail.html', context)


@user_passes_test(is_admin_cliente_or_gerente_check)
def product_update_view(request, pk):
    """Muestra y procesa el formulario de actualización de producto."""
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    
    # Define opciones de categoría para el GET/POST failure
    category_choices = Product.CATEGORY_CHOICES

    if request.method == 'POST':
        serializer = ProductSerializer(product, data=request.POST)
        
        if serializer.is_valid():
            serializer.save()
            messages.success(request, f"Producto '{product.name}' actualizado con éxito.")
            return redirect('products:product_detail', pk=pk)
        else:
            for field, errors in serializer.errors.items():
                messages.error(request, f"Error en {field}: {', '.join(errors)}")
            initial_data = request.POST # Use POST data for re-rendering errors

    else:
        # GET Request: Usar datos del modelo para la primera carga
        initial_data = model_to_dict(product)

    context = {
        'post_data': initial_data, 
        'product': product,
        'category_choices': category_choices # Pasa las opciones de categoría
    }
    return render(request, 'products/product_form.html', context)


# ----------------------------------------------------
# 2. PROVEEDORES (Admin Cliente / Gerente)
# ----------------------------------------------------

@user_passes_test(is_admin_cliente_or_gerente_check)
def supplier_list_view(request):
    """Muestra el listado de proveedores de la compañía (HTML)."""
    if response := check_company(request.user, request):
        return response
        
    suppliers = Supplier.objects.filter(company=request.user.company).order_by('name')
    return render(request, 'products/supplier_list.html', {'suppliers': suppliers})


@user_passes_test(is_admin_cliente_or_gerente_check)
def supplier_create_view(request):
    """Muestra y procesa el formulario de creación de proveedor."""
    if response := check_company(request.user, request):
        return response
    
    if request.method == 'POST':
        serializer = SupplierSerializer(data=request.POST)
        
        if serializer.is_valid():
            serializer.save(company=request.user.company)
            messages.success(request, "Proveedor registrado con éxito.")
            return redirect('products:supplier_list')
        else:
            for field, errors in serializer.errors.items():
                messages.error(request, f"Error en {field}: {', '.join(errors)}")
            
    context = {'post_data': request.POST if request.method == 'POST' else {}, 'user': request.user}
    return render(request, 'products/supplier_form.html', context)


@user_passes_test(is_admin_cliente_or_gerente_check)
def supplier_update_view(request, pk):
    """Muestra y procesa el formulario de actualización de proveedor."""
    supplier = get_object_or_404(Supplier, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        serializer = SupplierSerializer(supplier, data=request.POST)
        
        if serializer.is_valid():
            serializer.save() 
            messages.success(request, "Proveedor actualizado con éxito.")
            return redirect('products:supplier_list')
        else:
            for field, errors in serializer.errors.items():
                messages.error(request, f"Error en {field}: {', '.join(errors)}")

    else:
        initial_data = model_to_dict(supplier)

    context = {'post_data': initial_data, 'supplier': supplier}
    return render(request, 'products/supplier_form.html', context)


# ----------------------------------------------------
# 3. SUCURSALES (Admin Cliente)
# ----------------------------------------------------

@user_passes_test(is_admin_cliente_check)
def branch_list_view(request):
    """Muestra el listado de sucursales de la compañía (HTML)."""
    if response := check_company(request.user, request):
        return response
        
    branches = Branch.objects.filter(company=request.user.company).order_by('name')
    
    max_branches = request.user.company.subscription.max_branches if hasattr(request.user.company, 'subscription') else 0

    context = {
        'branches': branches,
        'branch_count': branches.count(),
        'max_branches': max_branches
    }
    return render(request, 'products/branch_list.html', context)


@user_passes_test(is_admin_cliente_check)
def branch_create_view(request):
    """Muestra y procesa el formulario de creación de sucursal (con límite de plan)."""
    if response := check_company(request.user, request):
        return response
    
    user = request.user
    context = {'user': user}

    if request.method == 'POST':
        # 1. Chequeo de Límite de Plan (Requisito clave)
        try:
            current_count = Branch.objects.filter(company=user.company).count()
            max_branches = user.company.subscription.max_branches
            
            if current_count >= max_branches:
                messages.error(request, f"Límite de Sucursales excedido. Tu plan actual solo permite {max_branches}. Considera actualizar tu suscripción.")
                return redirect('products:branch_list')
                
        except AttributeError:
             messages.error(request, "Error: La compañía no tiene un plan de suscripción definido.")
             return redirect('products:branch_list')

        # 2. Validación con Serializer
        data = request.POST.copy()
        serializer = BranchSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save(company=user.company)
            messages.success(request, f"Sucursal '{data['name']}' creada con éxito.")
            return redirect('products:branch_list')
        else:
            for field, errors in serializer.errors.items():
                messages.error(request, f"Error en {field}: {', '.join(errors)}")
            context['post_data'] = request.POST
            return render(request, 'products/branch_form.html', context)
            
    # GET Request
    context['post_data'] = {} # FIX: Inicializa post_data como diccionario vacío para GET
    return render(request, 'products/branch_form.html', context)


@user_passes_test(is_admin_cliente_check)
def branch_update_view(request, pk):
    """Muestra y procesa el formulario de actualización de sucursal."""
    # Placeholder para la lógica de edición
    messages.warning(request, "Implementación pendiente: Lógica de actualización de Sucursal.")
    return redirect('products:branch_list')


# ----------------------------------------------------
# 4. INVENTARIO (Listado HTML)
# ----------------------------------------------------

@user_passes_test(is_admin_cliente_or_gerente_check)
def inventory_list_view(request):
    """
    Muestra la interfaz HTML para la lista de inventario, filtrable por sucursal.
    """
    if response := check_company(request.user, request):
        return response
        
    branches = Branch.objects.filter(company=request.user.company)
    
    context = {
        'branches': branches,
    }
    # Renderiza la shell del inventario, la carga de datos es vía JS/API.
    return render(request, 'products/inventory_list.html', context)