# En usuarios/signals.py
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import PerfilUsuario

@receiver(post_save, sender=User)
def crear_o_actualizar_perfil_usuario(sender, instance, created, **kwargs):
    """
    Cada vez que un 'User' se crea, crea un 'PerfilUsuario' vacío.
    """
    if created:
        PerfilUsuario.objects.create(user=instance)