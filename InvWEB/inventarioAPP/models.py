import uuid
from django.db import models
from django.core.validators import MinValueValidator

class Categoria(models.Model):
    """
    Clasificación de los productos del inventario.
    Ej: Guantes, Mascarillas, Reactivos, Equipos, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    
 
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Producto del inventario (ej: Guantes de Nitrilo Talla M).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=150)
    sku = models.CharField(max_length=50, unique=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    descripcion = models.TextField(blank=True, null=True)
    unidad_medida = models.DecimalField(max_digits=10, decimal_places=2, default=1,validators=[MinValueValidator(0.01, message="La unidad de medida debe ser mayor que 0.")],verbose_name="Cantidad por Unidad")
    activo = models.BooleanField(default=True)
    stock_minimo = models.DecimalField(max_digits=10,decimal_places=2,default=5.0,verbose_name="Stock Mínimo (Paquetes)")
    

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.sku})"