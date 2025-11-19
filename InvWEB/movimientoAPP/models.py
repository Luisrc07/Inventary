# -------------------------------------------------------------------------
# Copyright (C) 2025 Luisrc07 - Luis Rodriguez
#
# Este programa es software libre: usted puede redistribuirlo y/o modificarlo
# bajo los términos de la Licencia Pública General GNU publicada
# por la Free Software Foundation, ya sea la versión 3 de la Licencia,
# o (a su elección) cualquier versión posterior.
#
# Este programa se distribuye con la esperanza de que sea útil, pero
# SIN NINGUNA GARANTÍA; sin incluso la garantía implícita de
# COMERCIABILIDAD o IDONEIDAD PARA UN PROPÓSITO PARTICULAR.
# Consulte la Licencia Pública General GNU para más detalles.
#
# Usted debería haber recibido una copia de la Licencia Pública General GNU
# junto con este programa. Si no, consulte <https://www.gnu.org/licenses/>.
# -------------------------------------------------------------------------

import uuid
from django.db import models, transaction
from departamentoAPP.models import Departamento
from inventarioAPP.models import Producto
from proveedorAPP.models import Proveedor
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from decimal import Decimal
from django.db.models import Q
# =========================================================================
# MODELO MOVIMIENTO 
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

    costo_unitario_usd = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Costo Unitario (USD) / Unidad"
    )
    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.tipo} de {self.producto.nombre} - {self.fecha.strftime('%d/%m/%Y')}"

 
    @property
    def costo_total_bs(self):
        if self.costo_unitario_bs and self.cantidad:
            return self.costo_unitario_bs * self.cantidad
        return None

    @property
    def ref_unitario_paquete_usd(self): 
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
        
        # Si es solo edición (no creación), guardamos normal y salimos
        if not is_creating:
            super().save(*args, **kwargs)
            return

        cantidad_paquetes = Decimal(str(self.cantidad)) 

        try:
            with transaction.atomic():
                # 1. Guardamos el Movimiento PRIMERO para que exista en DB
                super().save(*args, **kwargs)

                # 2. Manejo de Salidas (Resta stock)
                if self.tipo in ['SALIDA', 'TRANSFERENCIA']:
                    if not self.departamento_origen:
                        raise ValueError("Falta departamento origen")
                    
                    stock_origen, _ = StockActual.objects.get_or_create(
                        producto=self.producto,
                        departamento=self.departamento_origen
                    )
                    
                    if stock_origen.cantidad < cantidad_paquetes:
                        # Opcional: Lanzar error si no hay stock (Descomentar si deseas validación estricta)
                        # raise ValueError(f"Stock insuficiente. Disponible: {stock_origen.cantidad}")
                        pass 
                        
                    stock_origen.cantidad -= cantidad_paquetes
                    stock_origen.save()
                    
                    # Al reducir stock, recalculamos precio
                    stock_origen.recalcular_precio_maximo()

                # 3. Manejo de Entradas (Suma stock)
                if self.tipo in ['ENTRADA', 'TRANSFERENCIA']:
                    if not self.departamento_destino:
                        raise ValueError("Falta departamento destino")
                    
                    stock_destino, _ = StockActual.objects.get_or_create(
                        producto=self.producto,
                        departamento=self.departamento_destino
                    )
                    
                    stock_destino.cantidad += cantidad_paquetes
                    stock_destino.save()
                    
                    # Al aumentar stock, recalculamos precio
                    stock_destino.recalcular_precio_maximo()
                    
        except Exception as e:
            # Si falla la lógica, intentamos borrar el movimiento creado para no dejar basura
            # (Aunque transaction.atomic debería encargarse de revertir todo)
            raise ValueError(f"Error al procesar el stock: {str(e)}")
        
# =========================================================================
# MODELO STOCKACTUAL 
# =========================================================================
class StockActual(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    producto = models.ForeignKey('inventarioAPP.Producto', on_delete=models.PROTECT)
    departamento = models.ForeignKey('departamentoAPP.Departamento', on_delete=models.PROTECT, related_name='stock_items')
    
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # --- NUEVO CAMPO ---
    costo_maximo_vigente = models.DecimalField(
        max_digits=10, decimal_places=4, default=0, 
        verbose_name="Costo Más Alto en Stock (USD)"
    )

    class Meta:
        unique_together = ('producto', 'departamento')
        verbose_name = "Stock Actual"
        verbose_name_plural = "Stock Actual"

    def __str__(self):
        return f"{self.producto.nombre} - {self.departamento.nombre}: {self.cantidad}"

    # 1. CALCULAR EL VALOR TOTAL DEL INVENTARIO (Ej: 20 paquetes * 5$ = 100$)
    @property
    def valor_total_stock_usd(self):
        if self.cantidad and self.costo_maximo_vigente:
            return self.cantidad * self.costo_maximo_vigente
        return 0

    # 2. CALCULAR EL COSTO POR UNIDAD INDIVIDUAL (Ej: 5$ el paquete / 10 guantes = 0.50$ c/u)
    @property
    def costo_por_unidad_individual_usd(self):
        # Necesitamos que el producto tenga una unidad de medida mayor a 0 para dividir
        if (self.costo_maximo_vigente and self.producto.unidad_medida 
            and self.producto.unidad_medida > 0):
            return self.costo_maximo_vigente / self.producto.unidad_medida
        return 0
        
    @property
    def total_unidades(self):
        if self.cantidad and self.producto and self.producto.unidad_medida:
            return self.cantidad * self.producto.unidad_medida
        return 0

    # --- NUEVA LÓGICA DE RASTREO ---
    # En models.py dentro de StockActual
    
    def recalcular_precio_maximo(self):
        """
        Reconstruye el stock actual mirando hacia atrás, pero 
        DESCONTANDO las salidas intermedias para saber qué lotes 
        realmente siguen en existencia física.
        """
        from .models import Movimiento 

        if self.cantidad <= 0:
            self.costo_maximo_vigente = 0
            self.save(update_fields=['costo_maximo_vigente'])
            return

        # 1. Traemos TODOS los movimientos (Entradas Y Salidas) ordenados del más reciente al más viejo
        movimientos = Movimiento.objects.filter(
            producto=self.producto,
            # Filtramos por movimientos que afecten a este departamento (origen o destino)
            # Usamos Q objects para filtrar movimientos complejos si es necesario, 
            # pero para este algoritmo basta con saber si entró o salió de AQUÍ.
        ).filter(
            models.Q(departamento_destino=self.departamento) | 
            models.Q(departamento_origen=self.departamento)
        ).order_by('-fecha')

        stock_por_cubrir = self.cantidad
        salidas_acumuladas = Decimal(0) # "Deuda" de productos que salieron
        precios_encontrados = []

        for mov in movimientos:
            # Si ya cubrimos el stock físico actual, terminamos
            if stock_por_cubrir <= 0:
                break

            cantidad_mov = mov.cantidad

            # CASO A: Es una SALIDA (o Transferencia desde aquí)
            if (mov.tipo == 'SALIDA' and mov.departamento_origen == self.departamento) or \
               (mov.tipo == 'TRANSFERENCIA' and mov.departamento_origen == self.departamento):
                # Acumulamos deuda. Los próximos productos que entren (mirando hacia atrás)
                # se usarán para "pagar" esta salida, no para el stock actual.
                salidas_acumuladas += cantidad_mov
                continue

            # CASO B: Es una ENTRADA (o Transferencia hacia aquí)
            if (mov.tipo == 'ENTRADA' and mov.departamento_destino == self.departamento) or \
               (mov.tipo == 'TRANSFERENCIA' and mov.departamento_destino == self.departamento):
                
                # Si hay salidas pendientes ("deuda"), esta entrada se consume primero en ellas
                if salidas_acumuladas > 0:
                    if cantidad_mov > salidas_acumuladas:
                        # La entrada cubre toda la salida y sobra
                        cantidad_mov -= salidas_acumuladas
                        salidas_acumuladas = 0
                    else:
                        # La salida se consume toda esta entrada
                        salidas_acumuladas -= cantidad_mov
                        cantidad_mov = 0 # No sobra nada para el stock actual
                        continue # Pasamos al siguiente movimiento

                # Si después de pagar salidas, queda cantidad, esa es parte de nuestro stock actual
                if cantidad_mov > 0:
                    # Calculamos el precio real por paquete (tu corrección anterior)
                    costo_unitario = mov.costo_unitario_usd or 0
                    if self.producto.unidad_medida and self.producto.unidad_medida > 0:
                        precio_paquete = costo_unitario * self.producto.unidad_medida
                    else:
                        precio_paquete = costo_unitario

                    precios_encontrados.append(precio_paquete)
                    
                    # Restamos lo que tomamos de lo que necesitamos cubrir
                    stock_por_cubrir -= cantidad_mov

        # Calculamos el máximo de lo que realmente queda
        if precios_encontrados:
            self.costo_maximo_vigente = max(precios_encontrados)
        else:
            self.costo_maximo_vigente = 0
            
        self.save(update_fields=['costo_maximo_vigente'])