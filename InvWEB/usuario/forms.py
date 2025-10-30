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