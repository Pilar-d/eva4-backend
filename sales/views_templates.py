# sales/views_templates.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.db.models import F, Sum
from django.contrib import messages
from django.urls import reverse

# Importamos la función de chequeo para el Super Admin
from accounts.permissions import is_super_admin_check 
from accounts.permissions import is_vendedor_check # Needed for pos_sale_view

# Importar modelos
from .models import CartItem, ClientRequest 
from products.models import Product, Branch, Inventory
from accounts.models import User 
from core.models import Company

# ----------------------------------------------------
# 0. Request Delete View (Consolidated)
# ----------------------------------------------------
# This function was inserted out of order; placing it near the end, but before the main logic.

@user_passes_test(is_super_admin_check)
def request_delete_view(request, pk):
    """
    Procesa el POST para eliminar una solicitud de cliente.
    """
    if request.method == 'POST':
        solicitud = get_object_or_404(ClientRequest, pk=pk)
        
        # Impedir eliminar solicitudes que ya fueron aceptadas
        if solicitud.status != 'PENDIENTE':
             messages.error(request, f"La solicitud N°{pk} ya fue {solicitud.status} y no puede ser eliminada.")
        else:
             solicitud.delete()
             messages.success(request, f"Solicitud N°{pk} de {solicitud.company_name} eliminada con éxito.")

    # Redirects back to the list of requests
    return redirect('sales:request-list')


# ----------------------------------------------------
# 1. Catálogo de Productos (GET /shop/products/)
# ----------------------------------------------------

class CatalogoView(TemplateView):
    template_name = 'shop/catalogo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(company__is_active=True).order_by('name')
        return context

catalogo_view = CatalogoView.as_view()


# ----------------------------------------------------
# 2. Detalle de Producto (GET /shop/products/{id}/)
# ----------------------------------------------------

def detalle_producto_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    context = {
        'product': product,
    }
    return render(request, 'shop/detalle_producto.html', context)


# ----------------------------------------------------
# 3. Carrito de Compras (GET /shop/cart/)
# ----------------------------------------------------

@login_required(login_url='/login/')
def cart_view(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user).select_related('product')
    cart_total = sum(item.product.price * item.quantity for item in cart_items)

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_item_count': cart_items.count()
    }
    return render(request, 'shop/cart.html', context)


# ----------------------------------------------------
# 4. Checkout (GET /shop/checkout/)
# ----------------------------------------------------

@login_required(login_url='/login/')
def checkout_view(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user).select_related('product')

    if not cart_items.exists():
        messages.warning(request, "Tu carrito está vacío. No puedes proceder al checkout.")
        return redirect('shop:cart')

    cart_total = sum(item.product.price * item.quantity for item in cart_items)

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_item_count': cart_items.count()
    }
    return render(request, 'shop/checkout.html', context)


# ----------------------------------------------------
# 5. Dashboard (Vista para templates, usada por LOGIN_REDIRECT_URL)
# ----------------------------------------------------

def dashboard_view(request):
    """
    Vista que maneja el punto de entrada después del login.
    """
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    context = {'user': user}

    if user.company:
        try:
            context['subscription'] = user.company.subscription
            context['branch_count'] = Branch.objects.filter(company=user.company).count()
        except Exception:
            pass 

    return render(request, 'dashboard.html', context)

# ----------------------------------------------------
# 6. Vistas de Solicitud de Plan (Flujo de Nuevos Clientes)
# ----------------------------------------------------

def plan_request_view(request):
    """Muestra la interfaz para que los clientes envíen solicitudes de planes."""
    plans = [
        {'name': 'Básico', 'price': 19990, 'color': 'secondary', 'options': {'ecom': 3, 'branches': 1, 'reports': 'Básicos'}},
        {'name': 'Estándar', 'price': 39990, 'color': 'primary', 'options': {'ecom': 6, 'branches': 3, 'reports': 'Avanzados'}},
        {'name': 'Premium', 'price': 69990, 'color': 'success', 'options': {'ecom': 9, 'branches': 5, 'reports': 'Full API'}},
    ]
    
    # ⚠️ MODIFICACIÓN CLAVE: Renderiza la landing page completa
    return render(request, 'sales/plan_request_public_landing.html', {'plans': plans})


def submit_request(request):
    """Procesa el formulario POST de solicitud de cliente."""
    if request.method == 'POST':
        try:
            ClientRequest.objects.create(
                company_name=request.POST.get('company_name'),
                rut=request.POST.get('rut'),
                contact_email=request.POST.get('contact_email'),
                plan_name=request.POST.get('plan_name')
            )
            messages.success(request, "Su solicitud ha sido enviada con éxito. Pronto nos pondremos en contacto.")
        except Exception as e:
            messages.error(request, f"Error al procesar la solicitud: {e}")

        return redirect('shop:plan_request')
    return redirect('shop:plan_request')
    
# ----------------------------------------------------
# 7. Vista de Listado de Solicitudes (VISTA SUPER ADMIN)
# ----------------------------------------------------

@user_passes_test(is_super_admin_check)
def client_request_list_view(request):
    """
    Muestra la lista de solicitudes PENDIENTES de clientes al Super Admin.
    """
    pending_requests = ClientRequest.objects.filter(status='PENDIENTE').order_by('-created_at')
    
    return render(request, 'sales/request_admin_list.html', {'pending_requests': pending_requests})

# ----------------------------------------------------
# 8. POS Sale View (Vendedor)
# ----------------------------------------------------
# Added to resolve ImportError in sales/urls.py

@user_passes_test(is_vendedor_check)
def pos_sale_view(request):
    """
    Renders the Point of Sale (POS) interface.
    """
    from accounts.permissions import is_vendedor_check # Ensure check is available
    from django.db.models import F 
    
    user = request.user
    branch = None
    products_with_stock = []

    # Logic: Determine the seller's branch
    if user.company:
        branch = user.company.branch_set.first() # Simplification: use the first branch
        
        if branch:
            # Get products with stock in that branch (annotated stock)
            products_with_stock = Product.objects.filter(
                company=user.company,
                inventory__branch=branch,
                inventory__stock__gt=0
            ).annotate(inventory_stock=F('inventory__stock')).order_by('name')


    context = {
        'user': user,
        'branch': branch,
        'products': products_with_stock,
    }
    
    return render(request, 'sales/pos_sale.html', context)