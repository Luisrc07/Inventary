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

# En usuario/forms.py
from django import forms
from django.contrib.auth.models import User
from usuario.models import PerfilUsuario
from departamentoAPP.models import Departamento

class RegistroForm(forms.Form):
    
    # --- ¡LOS CAMPOS QUE FALTABAN ESTÁN AQUÍ! ---
    
    username = forms.CharField(
        label="Nombre de Usuario",
        max_length=100,
        required=True
    )
    
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput,
        required=True
    )
    
    rol = forms.ChoiceField(
        label="Rol del Usuario",
        choices=PerfilUsuario.ROL_CHOICES, # Usa los roles de tu models.py
        required=True
    )
    
    departamento = forms.ModelChoiceField(
        label="Departamento Asignado",
        queryset=Departamento.objects.filter(activo=True),
        required=False, # Es opcional, porque un Admin no necesita depto.
        help_text="Solo requerido si el Rol es Gerente u Operador."
    )
    
    # --- Tus métodos (estos ya estaban bien) ---

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get('rol')
        departamento = cleaned_data.get('departamento')

        # Esta validación la tenías en tu forms.py y es correcta 
        if rol != PerfilUsuario.ROL_ADMIN and not departamento:
            raise forms.ValidationError("Un Gerente o un Operador debe estar asignado a un departamento.")
        # [cite_end]
        
        # Validar que el username no exista
        username = cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")

        return cleaned_data

    def save(self):
        # Tu método save también es correcto 
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        
        perfil, created = PerfilUsuario.objects.get_or_create(user=user)
        perfil.rol = self.cleaned_data['rol']
        perfil.departamento = self.cleaned_data['departamento']
        perfil.save()
        # [cite_end]

        return user
    
class UserUpdateForm(forms.ModelForm):
    """
    Formulario para que el Admin edite el perfil Y
    los datos de login de un usuario.
    """
    
    # --- CAMPO AÑADIDO ---
    username = forms.CharField(
        label="Nombre de Usuario", 
        required=True
    )
    
    # --- CAMPO AÑADIDO ---
    password = forms.CharField(
        label="Nueva Contraseña", 
        required=False, 
        widget=forms.PasswordInput,
        help_text="Dejar en blanco para no cambiar la contraseña."
    )
    
    # Este campo ya lo tenías
    is_active = forms.BooleanField(
        label="Usuario Activo (Puede iniciar sesión)",
        required=False,
        help_text="Desmarca esto para desactivar al usuario (soft delete)."
    )

    class Meta:
        model = PerfilUsuario
        fields = ['rol', 'departamento'] # Campos del Perfil

    def __init__(self, *args, **kwargs):
        """
        Populamos los valores iniciales de 'is_active' y 'username'
        desde el modelo User.
        """
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            # Asigna el estado actual (True/False) del User al checkbox
            self.fields['is_active'].initial = self.instance.user.is_active
            
            # --- LÍNEA AÑADIDA ---
            # Asigna el nombre de usuario actual al campo de texto
            self.fields['username'].initial = self.instance.user.username

    def clean_username(self):
        """
        Valida que el nuevo nombre de usuario no esté ya en uso
        por OTRO usuario.
        """
        username = self.cleaned_data['username']
        
        # Busca si existe otro usuario (excluyendo el actual) con ese nombre
        if User.objects.filter(username=username).exclude(pk=self.instance.user.pk).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso por otra persona.")
        return username

    def save(self, commit=True):
        """
        Guardamos el Perfil Y los campos actualizados del User.
        """
        # 1. Obtiene el PerfilUsuario (rol, depto) pero no lo guarda aún
        perfil = super().save(commit=False) 
        
        # 2. Obtiene el objeto User relacionado
        user = perfil.user 

        # 3. Actualiza los campos del User desde nuestro formulario
        user.is_active = self.cleaned_data['is_active']
        user.username = self.cleaned_data['username']
        
        # 4. Revisa si se escribió una nueva contraseña
        new_password = self.cleaned_data.get('password')
        if new_password: # Solo si el campo no estaba vacío
            user.set_password(new_password) # ¡Usa set_password() para hashear!
        
        # 5. Guarda ambos objetos si commit=True
        if commit:
            user.save()
            perfil.save()
        
        return perfil