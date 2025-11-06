# Copyright (c) 2025, Luis Rodriguez.
# Este programa es software libre: puedes redistribuirlo y/o modificarlo
# bajo los términos de la Licencia Pública General GNU tal como está publicada
# por la Free Software Foundation, ya sea la versión 3 de la Licencia, o
# (a su elección) cualquier versión posterior.

# El Sistema de Inventario se distribuye con la esperanza de que sea útil,
# pero SIN NINGUNA GARANTÍA; ni siquiera la garantía implícita de
# COMERCIALIZACIÓN o IDONEIDAD PARA UN PROPÓSITO PARTICULAR. 
# Consulta la Licencia Pública General GNU para más detalles.

# Deberías haber recibido una copia de la Licencia Pública General GNU
# junto con este programa. Si no es así, consulta <https://www.gnu.org/licenses/>.

# -------------------
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal # <--- ¡IMPORTADO Y USADO PARA EVITAR EL ERROR DECIMAL/FLOAT!
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
    help = 'Crea datos de prueba extensos para gráficos (Departamentos, Productos, Usuarios, Stock y Movimientos).'
    
    # --- Datos Extensos y Variados para Gráficos ---
    DEPARTMENTS = ["Almacén Central", "Farmacia", "Cirugía", "Laboratorio", "Odontología", "Mantenimiento"]
    CATEGORIES = ["Medicamentos", "Insumos Quirúrgicos", "Material de Laboratorio", "Limpieza", "Herramientas","Mantenimiento"]
    PRODUCTS_DATA = {
        # Top 5 Productos Globales (Barra)
        "Jeringa 5cc (Paq x100)": ("Insumos Quirúrgicos", 100, 20), # Alto Stock
        "Gasa Estéril 10x10 (Caja)": ("Insumos Quirúrgicos", 20, 15), # Alto Stock
        "Cloruro de Sodio 0.9% (Unidad)": ("Medicamentos", 1, 8),
        "Guante de Látex (Caja x50)": ("Insumos Quirúrgicos", 50, 10),
        "Cuchilla Bisturí N°11 (Paq x10)": ("Insumos Quirúrgicos", 10, 5),
        
        # Productos para Alertas (Dashboard)
        "Batería AA Duracell (Paq x4)": ("Mantenimiento", 4, 15), # Stock muy bajo
        "Alcohol Isopropílico (Litro)": ("Material de Laboratorio", 1, 3), # Stock muy bajo
        
        # Productos variados para llenar la base
        "Analgésico Ibuprofeno 400mg": ("Medicamentos", 10, 5),
        "Kit de Sutura Estándar": ("Insumos Quirúrgicos", 1, 3),
        "Martillo de Bola 16oz": ("Herramientas", 1, 2),
    }
    
    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("--- Creando Datos de Prueba Extensos ---"))
        
        # Proveedor
        proveedor, _ = Proveedor.objects.get_or_create(
            nombre="Proveedor Principal Demo", defaults={'activo': True}
        )
        
        # 1. Crear Departamentos
        deptos = {}
        for name in self.DEPARTMENTS:
            depto, _ = Departamento.objects.get_or_create(nombre=name, defaults={'activo': True})
            deptos[name] = depto
        self.stdout.write(self.style.SUCCESS(f"Creados/Verificados {len(deptos)} Departamentos."))
        
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
                    'stock_minimo': Decimal(str(stock_min)), # Usamos Decimal
                    'activo': True,
                }
            )
            productos[name] = prod
        self.stdout.write(self.style.SUCCESS(f"Creados/Verificados {len(productos)} Productos."))
        
        # 4. Crear Usuarios de Prueba
        gerente_user, _ = User.objects.get_or_create(username='gerente', defaults={'email': 'gerente@test.com', 'is_staff': True})
        gerente_user.set_password('gerente123')
        gerente_user.save()
        
        operador_user, _ = User.objects.get_or_create(username='operador', defaults={'email': 'operador@test.com'})
        operador_user.set_password('operador123')
        operador_user.save()
        
        admin_user = User.objects.filter(username='admin').first()
        user_for_mov = admin_user if admin_user else gerente_user

        # Asignar Perfiles
        if PerfilUsuario:
            # Gerente: Rol GERENTE en Farmacia
            PerfilUsuario.objects.update_or_create(user=gerente_user, defaults={'rol': 'GERENTE', 'departamento': deptos["Farmacia"]})
            # Operador: Rol OPERADOR en Almacén Central
            PerfilUsuario.objects.update_or_create(user=operador_user, defaults={'rol': 'OPERADOR', 'departamento': deptos["Almacén Central"]})
            self.stdout.write(self.style.SUCCESS("Creados/Actualizados Perfiles de Gerente y Operador."))
        
        
        # 5. CREACIÓN DE MOVIMIENTOS ESTRATÉGICOS PARA GRÁFICOS
        self.stdout.write("\nCreando Movimientos Estratégicos...")
        
        TASA = Decimal('36.00')

        # --- A. Stock Alto para Top 5 y Gráfico de Departamento (Almacén Central domina) ---
        
        # 1. Producto Jeringa (Top 1 Global) - Mayoría en Almacén
        Movimiento.objects.create(
            tipo='ENTRADA', producto=productos["Jeringa 5cc (Paq x100)"],
            cantidad=Decimal('300.00'), # Alto stock en Almacén
            usuario_registra=user_for_mov, proveedor=proveedor, departamento_destino=deptos["Almacén Central"],
            numero_factura="FACT-A1", costo_unitario_bs=Decimal('15.00'), tasa_cambio=TASA,
            costo_unitario_usd=(Decimal('15.00') / TASA) / productos["Jeringa 5cc (Paq x100)"].unidad_medida
        )
        # 2. Producto Gasa (Top 2 Global) - Mayoría en Almacén
        Movimiento.objects.create(
            tipo='ENTRADA', producto=productos["Gasa Estéril 10x10 (Caja)"],
            cantidad=Decimal('250.00'), # Alto stock en Almacén
            usuario_registra=user_for_mov, proveedor=proveedor, departamento_destino=deptos["Almacén Central"],
            numero_factura="FACT-A2", costo_unitario_bs=Decimal('20.00'), tasa_cambio=TASA,
            costo_unitario_usd=(Decimal('20.00') / TASA) / productos["Gasa Estéril 10x10 (Caja)"].unidad_medida
        )

        # 3. Producto Cloruro (Stock medio)
        Movimiento.objects.create(
            tipo='ENTRADA', producto=productos["Cloruro de Sodio 0.9% (Unidad)"],
            cantidad=Decimal('100.00'),
            usuario_registra=user_for_mov, proveedor=proveedor, departamento_destino=deptos["Farmacia"],
            numero_factura="FACT-F1", costo_unitario_bs=Decimal('5.00'), tasa_cambio=TASA,
            costo_unitario_usd=(Decimal('5.00') / TASA) / productos["Cloruro de Sodio 0.9% (Unidad)"].unidad_medida
        )
        
        # --- B. Stock Medio/Bajo para otros departamentos ---
        
        # 4. Distribución variada para Farmacia
        Movimiento.objects.create(
            tipo='ENTRADA', producto=productos["Analgésico Ibuprofeno 400mg"],
            cantidad=Decimal('50.00'),
            usuario_registra=gerente_user, proveedor=proveedor, departamento_destino=deptos["Farmacia"],
            numero_factura="FACT-F2", costo_unitario_bs=Decimal('10.00'), tasa_cambio=TASA,
            costo_unitario_usd=(Decimal('10.00') / TASA) / productos["Analgésico Ibuprofeno 400mg"].unidad_medida
        )
        
        # 5. Distribución para Laboratorio
        Movimiento.objects.create(
            tipo='ENTRADA', producto=productos["Alcohol Isopropílico (Litro)"],
            cantidad=Decimal('20.00'),
            usuario_registra=user_for_mov, proveedor=proveedor, departamento_destino=deptos["Laboratorio"],
            numero_factura="FACT-L1", costo_unitario_bs=Decimal('30.00'), tasa_cambio=TASA,
            costo_unitario_usd=(Decimal('30.00') / TASA) / productos["Alcohol Isopropílico (Litro)"].unidad_medida
        )

        # 6. Distribución para Cirugía
        Movimiento.objects.create(
            tipo='ENTRADA', producto=productos["Kit de Sutura Estándar"],
            cantidad=Decimal('40.00'),
            usuario_registra=user_for_mov, proveedor=proveedor, departamento_destino=deptos["Cirugía"],
            numero_factura="FACT-C1", costo_unitario_bs=Decimal('80.00'), tasa_cambio=TASA,
            costo_unitario_usd=(Decimal('80.00') / TASA) / productos["Kit de Sutura Estándar"].unidad_medida
        )
        
        # --- C. Generar Alerta de Stock Mínimo ---
        
        # 7. Producto Batería (Stock Mantenimiento muy bajo)
        # Esto generará una ALERTA en el dashboard.
        Movimiento.objects.create(
            tipo='ENTRADA', producto=productos["Batería AA Duracell (Paq x4)"],
            cantidad=Decimal('5.00'), 
            usuario_registra=user_for_mov, proveedor=proveedor, departamento_destino=deptos["Mantenimiento"],
            numero_factura="FACT-M1", costo_unitario_bs=Decimal('40.00'), tasa_cambio=TASA,
            costo_unitario_usd=(Decimal('40.00') / TASA) / productos["Batería AA Duracell (Paq x4)"].unidad_medida
        )
        
        # --- D. Simular Salidas para Historial y reducir Top 5 ---
        
        # 8. Salida grande del Almacén Central
        Movimiento.objects.create(
            tipo='SALIDA', producto=productos["Jeringa 5cc (Paq x100)"],
            cantidad=Decimal('100.00'),
            usuario_registra=gerente_user, departamento_origen=deptos["Almacén Central"],
            observaciones="Transferencia a Farmacia no registrada, simulando salida."
        )

        self.stdout.write(self.style.SUCCESS("\n¡Seeder Extendido Finalizado!"))
        self.stdout.write(self.style.SUCCESS("------------------------------------"))
        self.stdout.write(self.style.SUCCESS(f"Gráficos listos para probarse."))
        self.stdout.write(self.style.SUCCESS(f"Usuario de prueba: 'gerente' (pass: gerente123)."))