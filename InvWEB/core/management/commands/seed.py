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
from django.contrib.auth.models import User
from django.db import transaction
import os

# Importa TODOS los modelos que quieres ELIMINAR
from movimientoAPP.models import Movimiento, StockActual
from inventarioAPP.models import Producto, Categoria
from departamentoAPP.models import Departamento
from proveedorAPP.models import Proveedor


class Command(BaseCommand):
    help = '¡BORRADO TOTAL! Limpia la BD (Movimientos, Stock, Productos, Deptos, etc.) y crea un admin.'

    @transaction.atomic # Si algo falla, se revierte toda la operación.
    def handle(self, *args, **kwargs):
        
        self.stdout.write(self.style.ERROR(
            "\n"
            "!!!!!!!!!!!!!!!!!!!! ¡ADVERTENCIA MÁXIMA! !!!!!!!!!!!!!!!!!!!!\n"
            "Este comando borrará TODOS LOS DATOS de las siguientes tablas:\n"
            "- Movimientos, StockActual, Productos, Categorías, Proveedores, Departamentos\n"
            "- Perfiles de Usuario (si se encuentran)\n"
            "- TODOS los Usuarios (EXCEPTO Superusuarios)\n"
            "\n"
            "¡ESTA ACCIÓN ES IRREVERSIBLE!\n"
        ))
        
        # 1. Pedir Confirmación (más estricta)
        respuesta = input("Escriba 'BORRAR' para confirmar la operación: ")
        if respuesta != 'BORRAR':
            self.stdout.write(self.style.ERROR("Operación cancelada."))
            return

        # ==============================================================
        # MANEJO SEGURO DE LA IMPORTACIÓN DEL MODELO DE PERFIL
        # ==============================================================
        PerfilUsuarioModel = None 
        try:
            # Importamos el modelo PerfilUsuario
            from usuario.models import PerfilUsuario
            PerfilUsuarioModel = PerfilUsuario 
            self.stdout.write(self.style.SUCCESS("\n  > Modelo 'PerfilUsuario' encontrado en 'usuarioAPP'."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f"\n  > No se pudo importar 'PerfilUsuario'. Error: {e}\n    (Se omitirá el borrado de Perfiles)."
            ))
        # ==============================================================

        # 2. Limpiar los Modelos (EL ORDEN ES CRÍTICO)
        self.stdout.write("\nLimpiando la base de datos (el orden es importante)...")
        
        try:
            # 1. ORDEN: Movimientos (liberan dependencias de Stock y Proveedores)
            total_mov, _ = Movimiento.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"  > {total_mov} Movimientos eliminados."))
            
            # 2. ORDEN: StockActual (libera dependencias de Producto/Depto)
            total_stock, _ = StockActual.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"  > {total_stock} Registros de Stock eliminados."))

            # 3. Borrar Perfiles (libera dependencias de User/Departamento)
            if PerfilUsuarioModel:
                total_perfil, _ = PerfilUsuarioModel.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f"  > {total_perfil} Perfiles de Usuario eliminados."))
            else:
                self.stdout.write(self.style.WARNING("  > Borrado de Perfiles de Usuario omitido."))
            
            # 4. Modelos intermedios y base
            total_prod, _ = Producto.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"  > {total_prod} Productos eliminados."))

            total_cat, _ = Categoria.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"  > {total_cat} Categorías eliminadas."))
            
            total_prov, _ = Proveedor.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"  > {total_prov} Proveedores eliminados."))

            total_depto, _ = Departamento.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"  > {total_depto} Departamentos eliminados."))
            
            # 5. Usuarios (SOLO los que NO son admin)
            total_user, _ = User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS(f"  > {total_user} Usuarios (no-admin) eliminados."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nError al limpiar la base de datos: {e}"))
            self.stdout.write(self.style.WARNING("La transacción se ha revertido. La base de datos no ha sido modificada."))
            return

        # 3. Crear el Superusuario por Defecto
        self.stdout.write("\nCreando superusuario por defecto y asignando rol ADMIN...")
        
        ADMIN_USER = os.environ.get('DJANGO_ADMIN_USER', 'admin')
        ADMIN_EMAIL = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@cecosesola.com')
        ADMIN_PASS = os.environ.get('DJANGO_ADMIN_PASS', 'admin123')

        # 3.1 Crear o buscar el usuario
        user, created = User.objects.get_or_create(
            username=ADMIN_USER,
            defaults={
                'email': ADMIN_EMAIL, 
                'is_staff': True, 
                'is_superuser': True,
            }
        )
        
        if created:
            user.set_password(ADMIN_PASS)
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f"  > Superusuario '{ADMIN_USER}' creado con contraseña '{ADMIN_PASS}'."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"  > El superusuario '{ADMIN_USER}' ya existía (no fue borrado). Actualizando perfil..."
            ))

        # 3.2 Asignar el perfil de administrador (si el modelo existe)
        if PerfilUsuarioModel:
            try:
                perfil, perfil_created = PerfilUsuarioModel.objects.update_or_create(
                    user=user,
                    defaults={
                        'rol': 'ADMIN', 
                        'departamento': None # Asegura que el admin no tenga departamento
                    }
                )
                if perfil_created:
                    self.stdout.write(self.style.SUCCESS("  > Perfil de Administrador (ADMIN) CREADO y asignado correctamente."))
                else:
                    self.stdout.write(self.style.SUCCESS("  > Perfil de Administrador (ADMIN) ACTUALIZADO correctamente."))
            except Exception as e:
                 self.stdout.write(self.style.ERROR(f"  > ERROR al crear/actualizar el PerfilUsuario: {e}"))
        
        self.stdout.write(self.style.SUCCESS(
            "\n¡Proceso de 'seed' (BORRADO TOTAL) completado exitosamente!"
        ))