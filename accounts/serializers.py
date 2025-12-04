# accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator 
from .utils import validar_rut 
from django.core.exceptions import ObjectDoesNotExist # Necesario para la comprobación

User = get_user_model() 

class UserSerializer(serializers.ModelSerializer):
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    # NO definimos 'rut' explícitamente aquí. Lo dejamos para el Meta.
    # El validador se aplicará en el método validate global.
    
    class Meta:
        model = User
        fields = (
            'id', 
            'username', 
            'email', 
            'rut', # <-- RUT se define aquí y usa la validación del modelo (unique=True)
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
            'rut': {'required': True} # Dejamos required:True aquí
        }

    def validate_rut(self, value):
        """
        Validación del RUT chileno (algoritmo DV) y limpieza.
        """
        rut_limpio = value.upper().replace('.', '').replace('-', '')
        
        # 1. Validación de formato (DV)
        if not validar_rut(rut_limpio):
            raise serializers.ValidationError("El RUT ingresado no es válido (falló el algoritmo DV).")
        
        return rut_limpio # Retornamos el valor limpio

    def validate(self, data):
        """
        Validación global del serializador, incluyendo unicidad del RUT después de la limpieza.
        """
        # El método validate_rut ya se ejecutó y limpió el RUT
        rut_limpio = data.get('rut')

        if rut_limpio:
            # 2. Validación de Unicidad
            # Comprobamos si el RUT limpio ya existe en la DB.
            try:
                # Si estamos actualizando un usuario, ignoramos al usuario actual (self.instance)
                existing_user = User.objects.get(rut=rut_limpio)
                if self.instance and existing_user.pk != self.instance.pk:
                    raise serializers.ValidationError({"rut": "Este RUT ya está registrado por otro usuario."})
                if not self.instance: # Si estamos creando
                    raise serializers.ValidationError({"rut": "Este RUT ya está registrado en el sistema."})
            except ObjectDoesNotExist:
                # Si no existe, es único y continuamos
                pass
            
            # 3. Sobrescribir el campo 'rut' con el valor limpio para el create/update
            data['rut'] = rut_limpio

        return data

    def create(self, validated_data):
        """
        Crear la cuenta de usuario, hasheando la contraseña.
        """
        # Aquí 'rut' ya está limpio debido al método validate()
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            rut=validated_data['rut'],
            role=validated_data['role'],
        )
        return user

    def update(self, instance, validated_data):
        """
        Manejo de la actualización del usuario.
        """
        # Aquí 'rut' ya está limpio debido al método validate()
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
            
        return user