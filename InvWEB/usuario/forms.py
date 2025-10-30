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
    Formulario para que el Admin edite el perfil de un usuario.
    """
    # 1. Añadimos el campo 'is_active' del modelo User
    is_active = forms.BooleanField(
        label="Usuario Activo (Puede iniciar sesión)",
        required=False,
        help_text="Desmarca esto para desactivar al usuario (soft delete)."
    )

    class Meta:
        model = PerfilUsuario
        fields = ['rol', 'departamento']

    def __init__(self, *args, **kwargs):
        """
        Populamos el valor inicial de 'is_active'
        desde el modelo User.
        """
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            # Asigna el estado actual (True/False) del User al checkbox
            self.fields['is_active'].initial = self.instance.user.is_active

    def save(self, commit=True):
        """
        Guardamos el Perfil Y el estado 'is_active' del User.
        """
        # 1. Guarda el PerfilUsuario (rol, departamento)
        perfil = super().save(commit=commit)
        
        # 2. Actualiza y guarda el User (is_active)
        if perfil.user:
            perfil.user.is_active = self.cleaned_data['is_active']
            if commit:
                perfil.user.save()
        
        return perfil