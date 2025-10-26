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
        Lógica de actualización de stock transaccional y segura,
        CON CÁLCULO DE UNIDAD DE MEDIDA.
        """
        
        if not self._state.adding:
            super().save(*args, **kwargs)
            return

        try:
            with transaction.atomic():
                
                # --- Validaciones y Lógica de Departamentos (igual que antes) ---
                if self.tipo == 'ENTRADA':
                    if not self.departamento_destino:
                        almacen_principal = Departamento.objects.filter(nombre__iexact='Almacén Principal').first()
                        if almacen_principal: self.departamento_destino = almacen_principal
                        else: raise ValueError("La ENTRADA debe tener un departamento de destino.")
                    if not self.proveedor:
                        raise ValueError("La ENTRADA debe tener un proveedor.")
                    self.departamento_origen = None

                elif self.tipo == 'SALIDA':
                    if not self.departamento_origen:
                        raise ValueError("La SALIDA debe tener un departamento de origen.")
                    self.departamento_destino = None

                elif self.tipo == 'TRANSFERENCIA':
                    if not self.departamento_origen or not self.departamento_destino:
                        raise ValueError("La TRANSFERENCIA debe tener origen y destino.")
                    if self.departamento_origen == self.departamento_destino:
                        raise ValueError("El origen y destino no pueden ser el mismo.")
                

                # --- ¡AQUÍ ESTÁ LA NUEVA LÓGICA! ---
                # 1. Obtenemos la unidad de medida del producto
                #    Usamos 'Decimal' para precisión monetaria/decimal.
                unidad_medida = self.producto.unidad_medida
                
                # 2. Calculamos la cantidad real de unidades a mover
                #    self.cantidad (ej. 2 cajas) * unidad_medida (ej. 100 guantes/caja)
                cantidad_real_a_mover = int(self.cantidad * unidad_medida)
                
                if cantidad_real_a_mover <= 0:
                     raise ValueError("La cantidad total a mover (Cantidad x Unidad de Medida) debe ser mayor a 0.")

                # --- Actualización de Stock (Usando cantidad_real_a_mover) ---
                
                # A. Restar de Origen (si aplica)
                if self.tipo in ['SALIDA', 'TRANSFERENCIA']:
                    stock_origen, created = StockActual.objects.get_or_create(
                        producto=self.producto,
                        departamento=self.departamento_origen,
                        defaults={'cantidad': 0}
                    )
                    
                    # Comparamos contra la cantidad REAL
                    if stock_origen.cantidad < cantidad_real_a_mover:
                        raise ValueError(f"No hay suficiente stock. Stock actual: {stock_origen.cantidad} unidades. Necesarias: {cantidad_real_a_mover} unidades.")
                    
                    stock_origen.cantidad -= cantidad_real_a_mover
                    stock_origen.save()

                # B. Sumar a Destino (si aplica)
                if self.tipo in ['ENTRADA', 'TRANSFERENCIA']:
                    stock_destino, created = StockActual.objects.get_or_create(
                        producto=self.producto,
                        departamento=self.departamento_destino,
                        defaults={'cantidad': 0}
                    )
                    stock_destino.cantidad += cantidad_real_a_mover
                    stock_destino.save()

                # 3. Guardar el movimiento
                super().save(*args, **kwargs)

        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Error inesperado al procesar el movimiento: {str(e)}")

class StockActual(models.Model):
    """
    Registra el stock disponible por producto y por departamento.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, related_name='stock_items')
    cantidad = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('producto', 'departamento')
        verbose_name = "Stock Actual"
        verbose_name_plural = "Stock Actual"

    def __str__(self):
        return f"{self.producto.nombre} - {self.departamento.nombre}: {self.cantidad}"