from django import forms 
from departamentoAPP.models import Encargado, Departamento
from django.forms import TextInput, Textarea, Select, NumberInput, EmailInput
from django.core.validators import RegexValidator


tailwind_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'

solo_numeros_validator = RegexValidator(
    regex=r'^\d+$', # Expresión regular que solo permite dígitos
    message="Este campo debe contener solo dígitos numéricos (0-9)."
)
class EncargadoForm(forms.ModelForm):
    telefono = forms.CharField(
        max_length=20,
        required=True,
        validators=[solo_numeros_validator],
        # APLICACIÓN DIRECTA DEL WIDGET CON ESTILOS
        widget=TextInput(attrs={
            'class': tailwind_class,
            'type': 'tel', # Mantiene el teclado numérico en móviles
            'placeholder': 'Solo números'
        })
    )
    class Meta:
        model= Encargado
        fields= ['nombres', 'apellidos', 'telefono', 'email', 'activo']
        widgets = {
            # ... (widgets para Encargado) ...
            
            'nombres': TextInput(attrs={'class': tailwind_class}),
            'apellidos': TextInput(attrs={'class': tailwind_class}),
            'email': EmailInput(attrs={'class': tailwind_class}),
        }




class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        fields = ['nombre','descripcion','encargado','activo']
        widgets= { 
        'nombre':TextInput(attrs={'class':tailwind_class}),
        'descipcion':Textarea(attrs={'class':tailwind_class}),
        'encargado':Select(attrs={'class':tailwind_class}),
        }           