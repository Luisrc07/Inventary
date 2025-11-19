# -------------------------------------------------------------------------
# Copyright (c) 2025, Luis Rodriguez.
# Este seeder ha sido actualizado para probar la lógica de Backtracking de Precios.
# -------------------------------------------------------------------------

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import random

# Importar TODOS los modelos
from departamentoAPP.models import Departamento
from inventarioAPP.models import Categoria, Producto
from proveedorAPP.models import Proveedor
from movimientoAPP.models import Movimiento, StockActual

# Manejo de la importación del modelo de Perfil
try:
    from usuario.models import PerfilUsuario
except ImportError:
    PerfilUsuario = None
    print("ADVERTENCIA: Modelo PerfilUsuario no encontrado. Solo se crearán Users.")


class Command(BaseCommand):
    help = 'Crea datos de prueba para verificar lógica de precios, stock y gráficos.'
    
    # --- Datos Maestros ---
    DEPARTMENTS = ["Almacén Central", "Farmacia", "Cirugía", "Laboratorio", "Odontología", "Mantenimiento"]
    CATEGORIES = ["Medicamentos", "Insumos Quirúrgicos", "Material de Laboratorio", "Limpieza", "Herramientas", "Mantenimiento"]
    
    # Formato: Nombre: (Categoría, Unidades_por_Paquete, Stock_Minimo)
    PRODUCTS_DATA = {
        # Top Productos
        "Jeringa 5cc (Paq x100)": ("Insumos Quirúrgicos", 100, 20),
        "Gasa Estéril 10x10 (Caja)": ("Insumos Quirúrgicos", 20, 15),
        "Cloruro de Sodio 0.9% (Unidad)": ("Medicamentos", 1, 8),
        
        # Producto para probar PRECIOS VARIADOS (Lógica FIFO/Max)
        "Guante de Látex (Caja x50)": ("Insumos Quirúrgicos", 50, 10),
        
        # Otros
        "Cuchilla Bisturí N°11 (Paq x10)": ("Insumos Quirúrgicos", 10, 5),
        "Batería AA Duracell (Paq x4)": ("Mantenimiento", 4, 15), 
        "Alcohol Isopropílico (Litro)": ("Material de Laboratorio", 1, 3),
        "Analgésico Ibuprofeno 400mg": ("Medicamentos", 10, 5),
        "Kit de Sutura Estándar": ("Insumos Quirúrgicos", 1, 3),
    }
    
    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("--- Iniciando Seeder Mejorado ---"))
        
        # 0. Crear Proveedor
        proveedor, _ = Proveedor.objects.get_or_create(
            nombre="Proveedor Global S.A.", defaults={'activo': True}
        )
        
        # 1. Crear Departamentos
        deptos = {}
        for name in self.DEPARTMENTS:
            depto, _ = Departamento.objects.get_or_create(nombre=name, defaults={'activo': True})
            deptos[name] = depto
        
        # 2. Crear Categorías
        categorias = {}
        for name in self.CATEGORIES:
            cat, _ = Categoria.objects.get_or_create(nombre=name)
            categorias[name] = cat
        
        # 3. Crear Productos
        productos = {}
        for name, (cat_name, unidad_medida, stock_min) in self.PRODUCTS_DATA.items():
            prod, _ = Producto.objects.get_or_create(
                nombre=name,
                defaults={
                    'categoria': categorias[cat_name],
                    'sku': name.split(' ')[0][:3].upper() + str(random.randint(100, 999)),
                    'unidad_medida': Decimal(str(unidad_medida)),
                    'stock_minimo': Decimal(str(stock_min)),
                    'activo': True,
                }
            )
            productos[name] = prod
        self.stdout.write(self.style.SUCCESS(f"Productos cargados: {len(productos)}"))
        
        # 4. Crear Usuarios
        gerente_user, _ = User.objects.get_or_create(username='gerente', defaults={'email': 'gerente@test.com', 'is_staff': True})
        if gerente_user._state.adding: gerente_user.set_password('gerente123'); gerente_user.save()
        
        operador_user, _ = User.objects.get_or_create(username='operador', defaults={'email': 'operador@test.com'})
        if operador_user._state.adding: operador_user.set_password('operador123'); operador_user.save()
        
        user_admin = User.objects.filter(is_superuser=True).first() or gerente_user

        if PerfilUsuario:
            PerfilUsuario.objects.update_or_create(user=gerente_user, defaults={'rol': 'GERENTE', 'departamento': deptos["Farmacia"]})
            PerfilUsuario.objects.update_or_create(user=operador_user, defaults={'rol': 'OPERADOR', 'departamento': deptos["Almacén Central"]})

        # =========================================================================
        # 5. CREACIÓN DE MOVIMIENTOS (Aquí probamos tu nueva lógica)
        # =========================================================================
        self.stdout.write("\nGenerando Movimientos...")
        
        # Tasa de prueba
        TASA = Decimal('40.00') 

        # --- A. Stock Base Normal ---
        Movimiento.objects.create(
            tipo='ENTRADA', producto=productos["Jeringa 5cc (Paq x100)"],
            cantidad=Decimal('300.00'),
            usuario_registra=user_admin, proveedor=proveedor, departamento_destino=deptos["Almacén Central"],
            numero_factura="FACT-001", costo_unitario_bs=Decimal('600.00'), tasa_cambio=TASA,
            # Costo Paquete 15$ -> Costo Unidad 0.15$
            costo_unitario_usd=Decimal('15.00') / productos["Jeringa 5cc (Paq x100)"].unidad_medida
        )

        Movimiento.objects.create(
            tipo='ENTRADA', producto=productos["Gasa Estéril 10x10 (Caja)"],
            cantidad=Decimal('50.00'),
            usuario_registra=user_admin, proveedor=proveedor, departamento_destino=deptos["Farmacia"],
            numero_factura="FACT-002", costo_unitario_bs=Decimal('200.00'), tasa_cambio=TASA,
            # Costo Paquete 5$
            costo_unitario_usd=Decimal('5.00') / productos["Gasa Estéril 10x10 (Caja)"].unidad_medida
        )

        # --- E. PRUEBA DE LÓGICA DE PRECIOS (Backtracking) ---
        # Producto: Guante de Látex (Caja x50) en Almacén Central
        # Vamos a meter precios variados para ver si el sistema elige el MAYOR vigente.
        
        prod_guantes = productos["Guante de Látex (Caja x50)"]
        depto_almacen = deptos["Almacén Central"]
        
        # 1. Entrada BARATA (Hace 3 días simulado - aunque aquí se crean al mismo tiempo, el orden de ID importa)
        # 10 Cajas a 5$ c/u
        Movimiento.objects.create(
            tipo='ENTRADA', producto=prod_guantes, cantidad=Decimal('10.00'),
            usuario_registra=user_admin, proveedor=proveedor, departamento_destino=depto_almacen,
            numero_factura="PRUEBA-LOW", costo_unitario_bs=Decimal('200.00'), tasa_cambio=TASA,
            costo_unitario_usd=Decimal('5.00') / prod_guantes.unidad_medida # 0.10 por guante
        )
        
        # 2. Entrada CARA (Hace 2 días)
        # 10 Cajas a 10$ c/u (El doble)
        # ALERTA: Al crear esto, tu sistema debería recalcular y poner el precio en 10$
        Movimiento.objects.create(
            tipo='ENTRADA', producto=prod_guantes, cantidad=Decimal('10.00'),
            usuario_registra=user_admin, proveedor=proveedor, departamento_destino=depto_almacen,
            numero_factura="PRUEBA-HIGH", costo_unitario_bs=Decimal('400.00'), tasa_cambio=TASA,
            costo_unitario_usd=Decimal('10.00') / prod_guantes.unidad_medida # 0.20 por guante
        )
        
        # 3. Entrada MEDIA (Hoy)
        # 5 Cajas a 8$ c/u
        # ALERTA: Aunque sea lo último que entró, el precio debería seguir siendo 10$ (porque aun quedan de las caras)
        Movimiento.objects.create(
            tipo='ENTRADA', producto=prod_guantes, cantidad=Decimal('5.00'),
            usuario_registra=user_admin, proveedor=proveedor, departamento_destino=depto_almacen,
            numero_factura="PRUEBA-MID", costo_unitario_bs=Decimal('320.00'), tasa_cambio=TASA,
            costo_unitario_usd=Decimal('8.00') / prod_guantes.unidad_medida # 0.16 por guante
        )

        # --- F. ALERTA DE STOCK BAJO ---
        Movimiento.objects.create(
            tipo='ENTRADA', producto=productos["Batería AA Duracell (Paq x4)"],
            cantidad=Decimal('2.00'), # Solo 2 paquetes, debería salir alerta
            usuario_registra=user_admin, proveedor=proveedor, departamento_destino=deptos["Mantenimiento"],
            numero_factura="FACT-LOW", costo_unitario_bs=Decimal('40.00'), tasa_cambio=TASA,
            costo_unitario_usd=Decimal('1.00') / productos["Batería AA Duracell (Paq x4)"].unidad_medida
        )

        self.stdout.write(self.style.SUCCESS("\n¡Seeder completado exitosamente!"))
        self.stdout.write(self.style.SUCCESS(f"Revisa los GUANTES en Almacén Central."))
        self.stdout.write(self.style.SUCCESS(f"Stock esperado: 25 Cajas."))
        self.stdout.write(self.style.SUCCESS(f"Precio esperado (Costo Paquete): 10.00 $ (El más alto de las entradas)."))