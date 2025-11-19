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
    def recalcular_precio_maximo(self):
        """
        Busca en el historial de entradas para cubrir la cantidad actual 
        y encuentra el precio más alto POR PAQUETE.
        """
        from .models import Movimiento 

        if self.cantidad <= 0:
            self.costo_maximo_vigente = 0
            self.save(update_fields=['costo_maximo_vigente'])
            return

        # Traemos las entradas más recientes
        entradas = Movimiento.objects.filter(
            producto=self.producto,
            departamento_destino=self.departamento,
            tipo__in=['ENTRADA', 'TRANSFERENCIA']
        ).order_by('-fecha')

        stock_por_cubrir = self.cantidad
        precios_encontrados = []

        for entrada in entradas:
            cant_entrada = entrada.cantidad
            
            # --- CORRECCIÓN AQUÍ ---
            # El movimiento guarda el costo de la UNIDAD pequeña (ej: 1 guante = 0.20$).
            # Pero el Stock se mide en PAQUETES (Cajas).
            # Debemos convertir ese costo unitario a COSTO POR PAQUETE.
            
            costo_individual_usd = entrada.costo_unitario_usd or 0
            
            # Multiplicamos por la unidad de medida del producto (ej: 0.20 * 50 = 10.00$)
            if self.producto.unidad_medida and self.producto.unidad_medida > 0:
                precio_paquete_real = costo_individual_usd * self.producto.unidad_medida
            else:
                precio_paquete_real = costo_individual_usd

            precios_encontrados.append(precio_paquete_real)
            # ------------------------

            stock_por_cubrir -= cant_entrada
            
            if stock_por_cubrir <= 0:
                break
        
        if precios_encontrados:
            self.costo_maximo_vigente = max(precios_encontrados)
        else:
            self.costo_maximo_vigente = 0
            
        self.save(update_fields=['costo_maximo_vigente'])