import uuid
from django.db import models
from departamentoAPP.models import Departamento
from inventarioAPP.models import Producto
from proveedorAPP.models import Proveedor

class Movimiento(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('SALIDA', 'Salida'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, blank=True, null=True)
    departamento_origen = models.ForeignKey(Departamento, on_delete=models.PROTECT, related_name='movimientos_origen', blank=True, null=True)
    departamento_destino = models.ForeignKey(Departamento, on_delete=models.PROTECT, related_name='movimientos_destino', blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} ({self.cantidad})"

    def save(self, *args, **kwargs):
        """
        Lógica de actualización de stock **directamente al guardar el movimiento**.
        """
        almacen_principal = Departamento.objects.filter(nombre__iexact='Almacén Principal').first()

        # Ajustar departamentos según tipo
        if self.tipo == 'ENTRADA':
            self.departamento_origen = None
            if almacen_principal and not self.departamento_destino:
                self.departamento_destino = almacen_principal

        elif self.tipo == 'SALIDA':
            self.departamento_destino = None
            if not self.departamento_origen:
                raise ValueError("Debe seleccionar un departamento de origen para SALIDA.")

        elif self.tipo == 'TRANSFERENCIA':
            if not self.departamento_origen or not self.departamento_destino:
                raise ValueError("Debe seleccionar origen y destino para TRANSFERENCIA.")

        super().save(*args, **kwargs)  # Guardar movimiento primero

        # Actualizar stock
        stock_destino, created = StockActual.objects.get_or_create(
            producto=self.producto,
            departamento=self.departamento_destino,
            defaults={'cantidad': 0}
        )
        stock_origen, created = StockActual.objects.get_or_create(
            producto=self.producto,
            departamento=self.departamento_origen,
            defaults={'cantidad': 0}
        )

        if self.tipo == 'ENTRADA':
            stock_destino.cantidad += self.cantidad
            stock_destino.save()

        elif self.tipo == 'SALIDA':
            if stock_origen.cantidad < self.cantidad:
                raise ValueError("No hay suficiente stock para realizar la SALIDA.")
            stock_origen.cantidad -= self.cantidad
            stock_origen.save()

        elif self.tipo == 'TRANSFERENCIA':
            if stock_origen.cantidad < self.cantidad:
                raise ValueError("No hay suficiente stock para realizar la TRANSFERENCIA.")
            stock_origen.cantidad -= self.cantidad
            stock_origen.save()
            stock_destino.cantidad += self.cantidad
            stock_destino.save()


class StockActual(models.Model):
    """
    Registra el stock disponible por producto y por departamento.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('producto', 'departamento')
        verbose_name = "Stock Actual"
        verbose_name_plural = "Stock Actual"

    def __str__(self):
        return f"{self.producto.nombre} - {self.departamento.nombre}: {self.cantidad}"
