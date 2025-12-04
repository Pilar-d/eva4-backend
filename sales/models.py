# sales/models.py
from django.db import models
from accounts.models import User
from products.models import Product, Branch
from core.models import Company

class Sale(models.Model):
    """Venta Presencial (POS)."""
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT, limit_choices_to={'role': 'vendedor'})
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Venta POS N°{self.id} en {self.branch.name}"

class SaleItem(models.Model):
    """Detalle de productos en una venta POS."""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Order(models.Model):
    """Venta en Línea (E-commerce)."""
    company = models.ForeignKey(Company, on_delete=models.PROTECT) 
    cliente_final_name = models.CharField(max_length=100)
    cliente_final_email = models.EmailField()
    
    STATUS_CHOICES = (
        ('PENDIENTE', 'Pendiente'), ('ENVIADO', 'Enviado'), ('ENTREGADO', 'Entregado'),
    )
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDIENTE')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

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
    quantity = models.IntegerField()

class ClientRequest(models.Model):
    """Solicitud de nuevo cliente desde la web pública (para Super Admin)."""
    company_name = models.CharField(max_length=100); rut = models.CharField(max_length=12)
    contact_email = models.EmailField(); plan_name = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default='PENDIENTE')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Solicitud de {self.company_name} ({self.plan_name})"