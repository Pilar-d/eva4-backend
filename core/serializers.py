# core/serializers.py

from rest_framework import serializers
from .models import Company, Subscription
from accounts.utils import validar_rut # Asumiendo que esta función está en accounts/utils.py

# ----------------------------------------------------
# 1. Serializer para Suscripción (anidado)
# ----------------------------------------------------

class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Subscription.
    Usado para mostrar el estado del plan de una Company.
    """
    # Muestra el nombre completo del plan en lugar del código ('BASICO' -> 'Básico')
    plan_display = serializers.CharField(source='get_plan_name_display', read_only=True) 

    class Meta:
        model = Subscription
        fields = (
            'id', 
            'plan_name', 
            'plan_display', 
            'start_date', 
            'end_date', 
            'active',
            'max_branches', # Muestra la restricción asociada al plan
        )
        read_only_fields = ('start_date', 'max_branches')

    def validate(self, data):
        """
        Validación de fechas: end_date debe ser posterior a start_date.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # Esta validación es importante para el POST o PUT si se modifica manualmente
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError("La fecha de término (end_date) debe ser posterior a la fecha de inicio (start_date).")
        
        return data


# ----------------------------------------------------
# 2. Serializer para Compañía (Tenant)
# ----------------------------------------------------

class CompanySerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Company. Incluye la suscripción anidada.
    """
    # Muestra el objeto de suscripción completo (relación OneToOne inversa)
    subscription = SubscriptionSerializer(read_only=True)
    
    class Meta:
        model = Company
        fields = (
            'id', 
            'name', 
            'rut', 
            'is_active', 
            'created_at', 
            'subscription'
        )
        read_only_fields = ('created_at', 'is_active')
        
    def validate_rut(self, value):
        """
        Validación del formato RUT (se asume que se usa la función de accounts/utils.py).
        """
        if not validar_rut(value):
            raise serializers.ValidationError("El RUT de la compañía no es válido.")
        return value
        
# ----------------------------------------------------
# 3. Serializer para la acción de Suscripción (POST /api/companies/{id}/subscribe/)
# ----------------------------------------------------

class SubscriptionActionSerializer(serializers.Serializer):
    """
    Serializador simple para manejar los datos del POST a /subscribe/.
    """
    plan_name = serializers.ChoiceField(
        choices=Subscription.PLAN_CHOICES, 
        required=True, 
        help_text="Plan a asignar (BASICO, ESTANDAR, PREMIUM)."
    )
    # Se podrían añadir campos como 'duration_months' para calcular el end_date si fuera necesario.