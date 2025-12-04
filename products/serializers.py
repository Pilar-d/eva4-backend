# products/serializers.py

from rest_framework import serializers
from django.db import transaction
from .models import Product, Branch, Supplier, Inventory
from accounts.utils import validar_rut # Asumimos la función validadora de RUT


# ----------------------------------------------------
# A. Inventario (Usado como anidado y para CRUD)
# ----------------------------------------------------

class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    branch_name = serializers.ReadOnlyField(source='branch.name')

    class Meta:
        model = Inventory
        fields = ('id', 'product', 'product_name', 'branch', 'branch_name', 'stock', 'reorder_point')
        read_only_fields = ('id',)

    def validate_stock(self, value):
        #[cite_start]"""Validación numérica: stock >= 0. [cite: 91, 201, 202]"""
        if value < 0:
            # Se permite stock negativo solo por ajustes con justificación, pero se prefiere >= 0
            raise serializers.ValidationError("El stock no puede ser negativo, excepto por ajustes justificados.")
        return value

# ----------------------------------------------------
# B. Serializadores de Entidades Principales
# ----------------------------------------------------

class ProductSerializer(serializers.ModelSerializer):
    # Campo ReadOnly para el tenant
    company_name = serializers.ReadOnlyField(source='company.name')
    
    class Meta:
        model = Product
        fields = ('id', 'sku', 'name', 'description', 'price', 'cost', 'category', 'company', 'company_name')
        read_only_fields = ('company',) # La compañía se asigna automáticamente

    def validate_price(self, value):
        #[cite_start]"""Validación numérica: price >= 0. [cite: 91, 199]"""
        if value < 0:
            raise serializers.ValidationError("El precio debe ser un valor positivo (>= 0).")
        return value

class BranchSerializer(serializers.ModelSerializer):
    # Muestra el inventario de la sucursal de forma anidada (opcional, pero útil)
    inventory = InventorySerializer(source='inventory_set', many=True, read_only=True)
    
    class Meta:
        model = Branch
        fields = ('id', 'name', 'address', 'phone', 'company', 'inventory')
        read_only_fields = ('company',)

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ('id', 'name', 'rut', 'contact', 'company')
        read_only_fields = ('company',)

    def validate_rut(self, value):
        #[cite_start]"""Validación del RUT chileno para el proveedor. [cite: 55, 87, 186, 188]"""
        rut_limpio = value.upper().replace('.', '').replace('-', '')
        if not validar_rut(rut_limpio):
            raise serializers.ValidationError("El RUT del proveedor no es válido (falla el algoritmo DV).")
        return rut_limpio

# ----------------------------------------------------
# C. Serializer para el ajuste manual de inventario
# ----------------------------------------------------

class InventoryAdjustSerializer(serializers.Serializer):
    """Usado para POST /api/inventory/adjust/"""
    branch_id = serializers.IntegerField(required=True)
    product_id = serializers.IntegerField(required=True)
    
    # Cantidad a sumar o restar (e.g., +5 o -2)
    adjustment_quantity = serializers.IntegerField(required=True) 
    justification = serializers.CharField(max_length=255, required=True)