# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import Company
from products.models import Branch # ⬅️ Importación para la sucursal de trabajo

class User(AbstractUser):
    """Modelo de Usuario Custom con control de roles y tenancy."""
    ROLE_CHOICES = (
        ('super_admin', 'Super Administrador'), 
        ('admin_cliente', 'Admin Cliente'),
        ('gerente', 'Gerente'),
        ('vendedor', 'Vendedor'),
        ('cliente_final', 'Cliente Final'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    rut = models.CharField(max_length=12, unique=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    
    # ⚠️ CAMPO AÑADIDO: Sucursal de trabajo para POS y gestión de inventario.
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Campos opcionales para login por email
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email', 'role', 'rut']
    
    def __str__(self):
        return self.username