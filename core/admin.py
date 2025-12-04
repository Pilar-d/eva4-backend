# core/admin.py

from django.contrib import admin
from .models import Company, Subscription

# ----------------------------------------------------
# 1. Inline para mostrar la Suscripción dentro de la Compañía
# ----------------------------------------------------

class SubscriptionInline(admin.StackedInline):
    """Permite editar la suscripción directamente desde la página de Company."""
    model = Subscription
    extra = 0 # No mostrar campos extra por defecto
    can_delete = False
    
    fieldsets = (
        (None, {'fields': ('plan_name', 'start_date', 'end_date', 'active')}),
        ('Restricciones de Plan', {'fields': ('max_branches',)}),
    )


# ----------------------------------------------------
# 2. Registro del modelo Company (Tenant)
# ----------------------------------------------------

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Administración de la cuenta cliente (Tenant)."""
    list_display = ('name', 'rut', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'rut')
    
    # Incluir el inline de Suscripción
    inlines = [SubscriptionInline]

    fieldsets = (
        (None, {'fields': ('name', 'rut', 'is_active')}),
        ('Fechas', {'fields': ('created_at',)}),
    )
    readonly_fields = ('created_at',)


# ----------------------------------------------------
# 3. Registro del modelo Subscription (opcional, si se requiere vista directa)
# ----------------------------------------------------

# @admin.register(Subscription)
# class SubscriptionAdmin(admin.ModelAdmin):
#     list_display = ('company', 'plan_name', 'active', 'start_date', 'end_date')
#     list_filter = ('plan_name', 'active')
#     readonly_fields = ('start_date',) 
#     search_fields = ('company__name',)