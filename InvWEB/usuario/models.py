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

from django.db import models
from django.contrib.auth.models import User
from departamentoAPP.models import Departamento

class PerfilUsuario(models.Model):
    """
    Este es tu modelo de 'Roles' personalizado.
    Conecta al Usuario de Django con un Rol y un Departamento.
    """
    
    # --- Definición de Roles ---
    ROL_ADMIN = 'ADMIN'
    ROL_GERENTE = 'GERENTE' # Gerente de Departamento
    ROL_OPERADOR = 'OPERADOR' # Almacenista/Operador
    
    ROL_CHOICES = [
        (ROL_ADMIN, 'Administrador General'),
        (ROL_GERENTE, 'Gerente de Departamento'),
        (ROL_OPERADOR, 'Operador de Departamento'),
    ]

    # --- Conexiones ---
    
    # Conexión 1:1 con el sistema de login de Django
    # Cada Usuario (login) tiene un solo Perfil (rol).
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')

    # Conexión con tu app de Departamentos
    # Un Admin puede no tener departamento (null=True)
    departamento = models.ForeignKey(
        Departamento, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Departamento al que pertenece el usuario (si no es Admin)",
        
        related_name='perfiles'
    )
    
    # Tu campo de Rol
    rol = models.CharField(
        max_length=10,
        choices=ROL_CHOICES,
        default=ROL_OPERADOR
    )

    def __str__(self):
        return f"{self.user.username} ({self.get_rol_display()})"

    # --- Funciones de ayuda para permisos ---
    @property
    def es_admin(self):
        return self.rol == self.ROL_ADMIN

    @property
    def es_gerente(self):
        return self.rol == self.ROL_GERENTE