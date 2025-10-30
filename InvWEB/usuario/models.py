
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
        help_text="Departamento al que pertenece el usuario (si no es Admin)"
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