import uuid
from django.db import models, transaction
from departamentoAPP.models import Departamento
from inventarioAPP.models import Producto
from proveedorAPP.models import Proveedor
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

# =========================================================================
# MODELO MOVIMIENTO (CORRECTO - USANDO DECIMAL)
# =========================================================================
class Movimiento(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('SALIDA', 'Salida'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    
    # Este campo ya es Decimal, lo cual es correcto.
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)], verbose_name="Cantidad (Paquetes)")
    
    # No borra el movimiento si se borra el usuario
    usuario_registra = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,verbose_name="Usuario que registra")

    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, blank=True, null=True)
    departamento_origen = models.ForeignKey(Departamento, on_delete=models.PROTECT, related_name='movimientos_origen', blank=True, null=True)
    departamento_destino = models.ForeignKey(Departamento, on_delete=models.PROTECT, related_name='movimientos_destino', blank=True, null=True)
    
    numero_factura = models.CharField(max_length=50, blank=True, null=True, verbose_name="N° Factura/Referencia")
    costo_unitario_bs = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Costo Unitario por paq(Bs.)")
    tasa_cambio = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Tasa de Cambio (Bs./USD)")

    fecha = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.tipo} de {self.producto.nombre} - {self.fecha.strftime('%d/%m/%Y')}"

    # ... (Tus propiedades @property costo_total_bs, ref_unitario_usd, total_unidades están bien) ...
    @property
    def costo_total_bs(self):
        if self.costo_unitario_bs and self.cantidad:
            return self.costo_unitario_bs * self.cantidad
        return None

    @property
    def ref_unitario_usd(self):
        if self.costo_unitario_bs and self.tasa_cambio and self.tasa_cambio > 0:
            return self.costo_unitario_bs / self.tasa_cambio
        return None
        
    @property
    def total_unidades(self):
        if self.cantidad and self.producto and self.producto.unidad_medida:
            return self.cantidad * self.producto.unidad_medida
        return None

    # LÓGICA DE GUARDADO CORREGIDA
    def save(self, *args, **kwargs):
        is_creating = self._state.adding
        
        # Si solo estamos editando (ej. observaciones), guardamos y salimos.
        if not is_creating:
            super().save(*args, **kwargs)
            return

        # La cantidad de stock a mover (en Paquetes)
        cantidad_paquetes = self.cantidad 

        try:
            # Envolvemos toda la lógica de stock Y el guardado del movimiento
            # en una sola transacción atómica.
            with transaction.atomic():
                
                # A. Restar de Origen (SALIDA O TRANSFERENCIA)
                if self.tipo in ['SALIDA', 'TRANSFERENCIA']:
                    if not self.departamento_origen:
                        raise ValueError("Debe especificar un Departamento de Origen para Salida/Transferencia.")
                    
                    stock_origen, created = StockActual.objects.get_or_create(
                        producto=self.producto,
                        departamento=self.departamento_origen,
                        defaults={'cantidad': 0}
                    )
                    
                    if stock_origen.cantidad < cantidad_paquetes:
                        raise ValueError(f"Stock insuficiente en {self.departamento_origen.nombre}. Disponible: {stock_origen.cantidad} Paquetes.")
                        
                    stock_origen.cantidad -= cantidad_paquetes
                    stock_origen.save()

                # B. Sumar a Destino (ENTRADA O TRANSFERENCIA)
                if self.tipo in ['ENTRADA', 'TRANSFERENCIA']:
                    if not self.departamento_destino:
                        raise ValueError("Debe especificar un Departamento de Destino para Entrada/Transferencia.")
                    
                    stock_destino, created = StockActual.objects.get_or_create(
                        producto=self.producto,
                        departamento=self.departamento_destino,
                        defaults={'cantidad': 0}
                    )
                    
                    stock_destino.cantidad += cantidad_paquetes
                    stock_destino.save()
                
                # 3. Si toda la lógica de stock fue exitosa, guardamos el Movimiento.
                super().save(*args, **kwargs)

        except ValueError as e:
            # Si algo falla (ej. "Stock insuficiente"), se revierte la transacción
            # y el Movimiento no se guarda.
            raise e
        except Exception as e:
            raise ValueError(f"Error inesperado al procesar el stock: {str(e)}")

# =========================================================================
# MODELO STOCKACTUAL (¡CAMBIO CRÍTICO!)
# =========================================================================
class StockActual(models.Model):
    """
    Registra el stock disponible por producto y por departamento.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, related_name='stock_items')
    
    # --- ¡ESTE ES EL CAMBIO MÁS IMPORTANTE! ---
    # Debe ser DecimalField para ser consistente con Movimiento.cantidad
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('producto', 'departamento')
        verbose_name = "Stock Actual"
        verbose_name_plural = "Stock Actual"

    def __str__(self):
        return f"{self.producto.nombre} - {self.departamento.nombre}: {self.cantidad}"
        
    @property
    def total_unidades(self):
        """Calcula el total de unidades (Paquetes * Unidad de Medida)."""
        if self.cantidad and self.producto and self.producto.unidad_medida:
            # Aseguramos que ambos sean decimales para la multiplicación
            return self.cantidad * self.producto.unidad_medida
        return 0