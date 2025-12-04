# accounts/permissions.py

from rest_framework.permissions import BasePermission
# Asegúrate de que este modelo se pueda importar (User)
from accounts.models import User 

# ----------------------------------------------------
# A. PERMISOS BASADOS EN CLASES (Para DRF ViewSets)
# ----------------------------------------------------

class IsSuperAdmin(BasePermission):
    """Permiso solo para el Super Administrador."""
    message = 'Acceso restringido. Requiere el rol de Super Administrador.'
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active and request.user.role == 'super_admin'

class IsAdminCliente(BasePermission):
    """Permiso solo para el Admin Cliente."""
    message = 'Acceso restringido. Requiere el rol de Administrador Cliente.'
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active and request.user.role == 'admin_cliente'

class IsGerente(BasePermission):
    """Permiso solo para el Gerente."""
    message = 'Acceso restringido. Requiere el rol de Gerente.'
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active and request.user.role == 'gerente'

class IsVendedor(BasePermission):
    """Permiso solo para el Vendedor."""
    message = 'Acceso restringido. Requiere el rol de Vendedor.'
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active and request.user.role == 'vendedor'

# --- Permisos Basados en Roles Múltiples ---

class IsAdminClienteOrGerente(BasePermission):
    """Permiso para Admin Cliente o Gerente (gestión de Productos/Inventario)."""
    message = 'Acceso restringido. Requiere el rol de Administrador Cliente o Gerente.'
    def has_permission(self, request, view):
        if not request.user.is_authenticated or not request.user.is_active:
            return False
        allowed_roles = ['admin_cliente', 'gerente']
        return request.user.role in allowed_roles

# --- PERMISO CUSTOM PARA LÓGICA OR (SOLUCIÓN AL ImportError) ---

class CustomOr(BasePermission):
    """
    Combina permisos usando lógica OR. Retorna True si AL MENOS uno de los 
    permisos anidados retorna True. (Implementación para DRF < 3.10).
    """
    def __init__(self, *permissions):
        # Almacena las instancias de las clases de permiso pasadas
        self.permissions = permissions

    def has_permission(self, request, view):
        # Itera sobre los permisos y retorna True tan pronto como uno pase.
        # Debe llamar al método has_permission de cada instancia de permiso.
        return any(perm.has_permission(request, view) for perm in self.permissions)

# --- Permisos de Nivel de Objeto (Tenancy) ---

class IsOwnerOrReadOnly(BasePermission):
    """
    Permite el acceso de escritura solo si el objeto pertenece a la compañía del usuario
    o si el usuario es Super Admin.
    """
    message = 'No tienes permiso para modificar datos de otras compañías.'
    
    def has_object_permission(self, request, view, obj):
        # Permite la lectura (GET, HEAD, OPTIONS)
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        
        # Super Admin siempre puede modificar cualquier objeto
        if request.user.role == 'super_admin':
            return True
            
        # CORRECCIÓN DE SEGURIDAD: Solo permitir si el usuario tiene una compañía asignada
        if not request.user.company:
            return False

        # Verifica si el objeto tiene un campo 'company' (Tenancy check)
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
            
        return False
        
# ----------------------------------------------------
# B. FUNCIÓN DE CHEQUEO (Para Decoradores de Django)
# ----------------------------------------------------

def is_super_admin_check(user):
    """
    Función de verificación de Super Admin para decoradores de Django (@user_passes_test).
    """
    # Verifica que el usuario esté autenticado, activo y tenga el rol 'super_admin'
    return user.is_authenticated and user.is_active and user.role == 'super_admin'

def is_admin_cliente_or_gerente_check(user):
    """Verifica si el usuario es Admin Cliente O Gerente (para CRUD de gestión)."""
    return user.is_authenticated and user.is_active and user.role in ['admin_cliente', 'gerente']

def is_admin_cliente_check(user):
    """Verifica si el usuario es Admin Cliente (para CRUD de sucursales/personal)."""
    return user.is_authenticated and user.is_active and user.role == 'admin_cliente'

def is_vendedor_check(user):
    """Verifica si el usuario es Vendedor."""
    return user.is_authenticated and user.is_active and user.role == 'vendedor'