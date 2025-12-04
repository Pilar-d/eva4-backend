# accounts/admin.py (CORRECCIÓN DE FIELDSETS)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    
    list_display = (
        'username', 
        'email', 
        'role', 
        'company', 
        'is_active', 
        'is_staff',
    )
    
    list_filter = (
        'role', 
        'is_active', 
        'company', 
        'is_staff', 
        'is_superuser'
    )
    
    search_fields = ('username', 'email', 'rut')
    readonly_fields = ('created_at',)

    # CORRECCIÓN AQUÍ: Aseguramos que 'is_active' no se duplique.
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email', 'rut')}),
        # 1. Dejamos 'is_active' aquí (Roles y estado de la cuenta):
        ('Roles y Compañía', {'fields': ('role', 'company', 'is_active')}), 
        
        # 2. Eliminamos 'is_active' del grupo de Permisos.
        ('Permisos', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'), # is_active ELIMINADO
        }),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined', 'created_at')}),
    )

    # El add_fieldsets no necesita cambios si los campos no se duplican.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'rut', 'role', 'company', 'is_staff', 'is_superuser', 'password'),
        }),
    )