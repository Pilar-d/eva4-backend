# accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .utils import validar_rut # Función validadora del RUT chileno

User = get_user_model() # Obtener el modelo de usuario custom

class UserSerializer(serializers.ModelSerializer):
    
    # Campo para mostrar el nombre legible del rol, no solo el código
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 
            'username', 
            'email', 
            'rut', 
            'role', 
            'role_display',
            'is_active', 
            'company', 
            'created_at', 
            'password'
        )
        read_only_fields = ('created_at', 'is_active', 'company')
        extra_kwargs = {
            'password': {'write_only': True, 'required': True, 'min_length': 8},
            'email': {'required': True},
            'rut': {'required': True}
        }

    def validate_rut(self, value):
        """
        Validación del RUT chileno (algoritmo DV).
        """
        # Limpiar y validar
        rut_limpio = value.upper().replace('.', '').replace('-', '')
        if not validar_rut(rut_limpio):
            raise serializers.ValidationError("El RUT ingresado no es válido (falló el algoritmo DV).")
        return rut_limpio

    def create(self, validated_data):
        """
        Crear la cuenta de usuario, hasheando la contraseña.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            rut=validated_data['rut'],
            role=validated_data['role'],
            # Los campos company e is_active se pueden sobrescribir en perform_create
        )
        return user

    def update(self, instance, validated_data):
        """
        Manejo de la actualización del usuario (si se permite). 
        Se asegura que la contraseña se hashee si se cambia.
        """
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
            
        return user