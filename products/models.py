# products/models.py
from django.db import models
from core.models import Company
from django.db.models import Sum

class Supplier(models.Model):
    # ... (Modelo Supplier es correcto) ...
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    rut = models.CharField(max_length=12) 
    contact = models.CharField(max_length=100)

    class Meta:
        unique_together = (('company', 'rut'),)
        
    def __str__(self):
        return self.name

class Product(models.Model):
    # Definición de las 20 opciones de categoría (Mantenido)
    CATEGORY_CHOICES = (
        ('ALIMENTOS', 'Alimentos y Comestibles'),
        ('BEBIDAS', 'Bebidas y Licores'),
        ('SNACKS', 'Snacks y Confitería'),
        ('LIMPIEZA', 'Productos de Limpieza'),
        ('HIGIENE', 'Higiene Personal'),
        ('FARMACIA', 'Medicamentos / Farmacia'),
        ('TECNOLOGIA', 'Electrónica y Tecnología'),
        ('HOGAR', 'Artículos para el Hogar'),
        ('JUGUETES', 'Juguetes'),
        ('ROPA', 'Vestimenta y Accesorios'),
        ('DEPORTES', 'Deportes'),
        ('JARDIN', 'Jardinería'),
        ('MASCOTAS', 'Productos para Mascotas'),
        ('LIBROS', 'Libros y Papelería'),
        ('VEHICULOS', 'Accesorios para Vehículos'),
        ('HERRAMIENTAS', 'Herramientas'),
        ('SERVICIOS', 'Servicios'),
        ('CONGELADOS', 'Congelados'),
        ('FRESCOS', 'Productos Frescos'),
        ('OTROS', 'Otros / Varios'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES) 
    
    # ⚠️ Si se necesitara un campo de unidades por paquete:
    # units_per_package = models.IntegerField(default=1) 
    
    class Meta:
        ordering = ['name']
        unique_together = (('company', 'sku'),)
        
    def __str__(self):
        return self.name
        
    # Método para obtener el stock total (se usaría en vistas, no en migraciones)
    def get_total_stock(self):
        return self.inventory_set.aggregate(total_stock=Sum('stock'))['total_stock'] or 0

class Branch(models.Model):
    # ... (Modelo Branch es correcto) ...
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    products = models.ManyToManyField(Product, through='Inventory')

    def __str__(self):
        return f"{self.name} ({self.company.name})"

class Inventory(models.Model):
    """Relación Branch x Product con stock y punto de reorden."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    stock = models.IntegerField()
    reorder_point = models.IntegerField(default=0)

    class Meta:
        unique_together = ('product', 'branch')
        
    def __str__(self):
        return f"{self.product.name} en {self.branch.name} (Stock: {self.stock})"