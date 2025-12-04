# core/models.py
from django.db import models
from datetime import timedelta
from django.utils import timezone

class Company(models.Model):
    """Representa a cada cliente (Tenant) de TemucoSoft."""
    name = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True, help_text="RUT del cliente (con o sin guión/puntos)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Subscription(models.Model):
    """Modelo para la suscripción y planes de cada Company."""
    PLAN_CHOICES = (
        ('BASICO', 'Básico'),
        ('ESTANDAR', 'Estándar'),
        ('PREMIUM', 'Premium'),
    )
    
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='subscription')
    plan_name = models.CharField(max_length=20, choices=PLAN_CHOICES)
    
    # Dates
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    active = models.BooleanField(default=False)

    # Restricción (para lógica de plan)
    max_branches = models.IntegerField(default=1)

    def save(self, *args, **kwargs):
        # 1. Asegura que start_date esté establecido si es un objeto nuevo
        if not self.start_date:
            self.start_date = timezone.now().date()

        # 2. Calcula end_date si es necesario (para evitar fallos NOT NULL)
        if not self.end_date or self._state.adding:
            if self.plan_name == 'BASICO':
                duration = timedelta(days=30)
            elif self.plan_name == 'ESTANDAR':
                duration = timedelta(days=90)
            elif self.plan_name == 'PREMIUM':
                duration = timedelta(days=365)
            else:
                duration = timedelta(days=30)
                 
            self.end_date = self.start_date + duration

        # 3. Asigna restricciones según el plan
        if self.plan_name == 'BASICO':
            self.max_branches = 3
        elif self.plan_name == 'ESTANDAR':
            self.max_branches = 6
        elif self.plan_name == 'PREMIUM':
            self.max_branches = 9
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company.name} - {self.get_plan_name_display()}"