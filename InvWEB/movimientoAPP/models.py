# En movimientoAPP/modelsmov.py

import uuid
from django.db import models, transaction  # ¡Importante!
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
        Lógica de actualización de stock transaccional y segura.
        """
        
        # 1. Solo ejecutar la lógica de stock si es un MOVIMIENTO NUEVO.
        # Esto evita que se duplique el stock si alguien edita un movimiento.
        if not self._state.adding:
            super().save(*args, **kwargs) # Solo guarda los cambios (ej. una 'observación')
            return # Y no ejecuta la lógica de stock de abajo

        # 2. Envolver toda la lógica en una transacción atómica
        # Si algo falla (ej. no hay stock), NADA se guarda. Ni el stock NI el movimiento.
        try:
            with transaction.atomic():
                
                # --- Validaciones y Lógica de Departamentos ---
                if self.tipo == 'ENTRADA':
                    if not self.departamento_destino:
                        # Intenta asignar al almacén principal por defecto
                        almacen_principal = Departamento.objects.filter(nombre__iexact='Almacén Principal').first()
                        if almacen_principal:
                            self.departamento_destino = almacen_principal
                        else:
                            raise ValueError("La ENTRADA debe tener un departamento de destino.")
                    if not self.proveedor:
                        raise ValueError("La ENTRADA debe tener un proveedor.")
                    self.departamento_origen = None # Aseguramos que sea nulo

                elif self.tipo == 'SALIDA':
                    if not self.departamento_origen:
                        raise ValueError("La SALIDA debe tener un departamento de origen.")
                    self.departamento_destino = None # Aseguramos que sea nulo

                elif self.tipo == 'TRANSFERENCIA':
                    if not self.departamento_origen or not self.departamento_destino:
                        raise ValueError("La TRANSFERENCIA debe tener origen y destino.")
                    if self.departamento_origen == self.departamento_destino:
                        raise ValueError("El origen y destino no pueden ser el mismo.")
                
                # --- Actualización de Stock (Lógica Central) ---
                
                # A. Restar de Origen (si aplica)
                if self.tipo in ['SALIDA', 'TRANSFERENCIA']:
                    stock_origen, created = StockActual.objects.get_or_create(
                        producto=self.producto,
                        departamento=self.departamento_origen,
                        defaults={'cantidad': 0}
                    )
                    
                    if stock_origen.cantidad < self.cantidad:
                        raise ValueError(f"No hay suficiente stock de '{self.producto.nombre}' en '{self.departamento_origen.nombre}'.")
                    
                    stock_origen.cantidad -= self.cantidad
                    stock_origen.save()

                # B. Sumar a Destino (si aplica)
                if self.tipo in ['ENTRADA', 'TRANSFERENCIA']:
                    stock_destino, created = StockActual.objects.get_or_create(
                        producto=self.producto,
                        departamento=self.departamento_destino,
                        defaults={'cantidad': 0}
                    )
                    stock_destino.cantidad += self.cantidad
                    stock_destino.save()

                # 3. Guardar el movimiento (SOLO si toda la lógica de stock fue exitosa)
                super().save(*args, **kwargs)

        except ValueError as e:
            # Si se lanzó un ValueError (ej. "No hay stock"), lo relanzamos
            # para que el admin de Django o el Serializer lo muestre al usuario.
            raise e
        except Exception as e:
            # Capturar cualquier otro error inesperado
            raise ValueError(f"Error inesperado al procesar el movimiento: {str(e)}")


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