import uuid
from django.db import models


class Encargado(models.Model):
    """
    Representa a una persona responsable de un departamento.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Encargado"
        verbose_name_plural = "Encargados"
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"


class Departamento(models.Model):
    """
    Un departamento o área dentro de la institución.
    Cada departamento puede tener un encargado.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    encargado = models.ForeignKey(
        Encargado, on_delete=models.SET_NULL, null=True, blank=True, related_name='departamentos'
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre