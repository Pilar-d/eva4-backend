# sales/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import Sale, SaleItem, Order, OrderItem, CartItem
from products.models import Inventory, Product # Necesario para actualizar stock

# ----------------------------------------------------
# A. Venta Presencial (POS)
# ----------------------------------------------------

class SaleItemSerializer(serializers.ModelSerializer):
    """Serializador para el detalle de un ítem dentro de una Venta POS."""
    class Meta:
        model = SaleItem
        fields = ('product', 'quantity', 'price')

    def validate_quantity(self, value):
        """Validación numérica: quantity >= 1."""
        if value < 1:
            raise serializers.ValidationError("La cantidad debe ser al menos 1.")
        return value

class SaleSerializer(serializers.ModelSerializer):
    """Serializador principal para registrar una Venta POS."""
    items = SaleItemSerializer(many=True, write_only=True) # Acepta una lista de ítems para crear la venta

    class Meta:
        model = Sale
        fields = ('id', 'branch', 'user', 'total', 'payment_method', 'created_at', 'items')
        read_only_fields = ('user', 'total', 'created_at')

    def validate_created_at(self, value):
        """Validación de fechas: Sale.created_at no puede estar en el futuro."""
        if value > timezone.now():
            raise serializers.ValidationError("La fecha de venta no puede estar en el futuro.")
        return value

    def validate(self, data):
        """
        Validación a nivel de objeto para verificar si la lista de ítems está vacía
        y si el total es positivo.
        """
        if not data.get('items'):
            raise serializers.ValidationError("La venta debe contener al menos un ítem.")
        
        # El total se calcula en la vista, pero se podría validar si se enviara
        return data
        
    # El método create() se implementará en el ViewSet usando lógica transaccional (perform_create)

# ----------------------------------------------------
# B. E-commerce (Orders y Cart)
# ----------------------------------------------------

class CartItemSerializer(serializers.ModelSerializer):
    """Serializador para el modelo temporal CartItem."""
    product_name = serializers.ReadOnlyField(source='product.name')
    
    class Meta:
        model = CartItem
        fields = ('id', 'user', 'product', 'product_name', 'quantity')
        read_only_fields = ('user',)

    def validate_quantity(self, value):
        """Validación numérica: CartItem.quantity >= 1."""
        if value < 1:
            raise serializers.ValidationError("La cantidad de ítems debe ser al menos 1.")
        return value

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('product', 'quantity', 'price')

class OrderSerializer(serializers.ModelSerializer):
    """Serializador para el modelo Order (resultado del checkout)."""
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'company', 'cliente_final_name', 'cliente_final_email', 'estado', 'total', 'created_at', 'items')
        read_only_fields = ('company', 'total', 'created_at', 'estado')

# ----------------------------------------------------
# C. Compras / Ingreso de Stock
# ----------------------------------------------------

class PurchaseCreateSerializer(serializers.Serializer):
    """
    Serializador para registrar una compra a proveedor (que incrementa stock).
    Se usa para POST /api/purchases/
    """
    supplier_id = serializers.IntegerField()
    branch_id = serializers.IntegerField(help_text="Sucursal donde ingresará el stock.")
    date = serializers.DateField(help_text="Fecha de la compra.")
    
    # Lista de productos comprados
    items = SaleItemSerializer(many=True) 

    def validate_date(self, value):
        """Validación de fechas: Purchase.date no mayor a hoy."""
        if value > timezone.now().date():
            raise serializers.ValidationError("La fecha de compra no puede ser futura.")
        return value