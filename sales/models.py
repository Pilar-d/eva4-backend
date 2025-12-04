# sales/models.py
from django.db import models
from accounts.models import User
from products.models import Product, Branch

class Sale(models.Model):
    """Venta Presencial (POS)."""
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT) # [cite: 61]
    user = models.ForeignKey(User, on_delete=models.PROTECT, limit_choices_to={'role': 'vendedor'}) # [cite: 61]
    total = models.DecimalField(max_digits=10, decimal_places=2) # [cite: 61]
    payment_method = models.CharField(max_length=50) # [cite: 61]
    created_at = models.DateTimeField(auto_now_add=True) # [cite: 61, 90]

    def __str__(self):
        return f"Venta POS N°{self.id} en {self.branch.name}"

class SaleItem(models.Model):
    """Detalle de productos en una venta POS."""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField() # [cite: 61]
    price = models.DecimalField(max_digits=10, decimal_places=2) # Precio de venta al momento de la transacción [cite: 61]

class Order(models.Model):
    """Venta en Línea (E-commerce)."""
    company = models.ForeignKey(Product, on_delete=models.PROTECT) # Para asegurar la pertenencia
    cliente_final_name = models.CharField(max_length=100) # [cite: 62]
    cliente_final_email = models.EmailField() # [cite: 62]
    
    STATUS_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('ENVIADO', 'Enviado'),
        ('ENTREGADO', 'Entregado'),
    )
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDIENTE') # [cite: 62]
    total = models.DecimalField(max_digits=10, decimal_places=2) # [cite: 62]
    created_at = models.DateTimeField(auto_now_add=True) # [cite: 62]

class OrderItem(models.Model):
    """Detalle de productos en una Order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

class CartItem(models.Model):
    """Modelo temporal para el carro de compras de un usuario logueado (opcional)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField() # [cite: 203]

# sales/models.py (Fragmento)
class ClientRequest(models.Model):
    company_name = models.CharField(max_length=100)
    rut = models.CharField(max_length=12)
    contact_email = models.EmailField()
    plan_name = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default='PENDIENTE') # PENDIENTE/ACEPTADO/RECHAZADO
    created_at = models.DateTimeField(auto_now_add=True)
    # Opcional: admin_note = models.TextField()