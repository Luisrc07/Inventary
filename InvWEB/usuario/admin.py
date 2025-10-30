from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PerfilUsuario

# Define un "inline" para que el Perfil se muestre DENTRO del Usuario
class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil de Usuario (Rol)'

# Define un nuevo Administrador de Usuarios que incluye el Perfil
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)

# Vuelve a registrar el modelo User con nuestro nuevo Admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# (Opcional) Registra también PerfilUsuario por separado
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'departamento')
    list_filter = ('rol', 'departamento')