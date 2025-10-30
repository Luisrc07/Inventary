from django import forms 
from departamentoAPP.models import Departamento
from django.forms import TextInput, Textarea, Select, NumberInput, EmailInput
from django.core.validators import RegexValidator


tailwind_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'

solo_numeros_validator = RegexValidator(
    regex=r'^\d+$', # Expresión regular que solo permite dígitos
    message="Este campo debe contener solo dígitos numéricos (0-9)."
)




class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        fields = ['nombre','descripcion','activo']
        widgets= { 
        'nombre':TextInput(attrs={'class':tailwind_class}),
        'descripcion': Textarea(attrs={'class': tailwind_class, 'rows':2}),
        'encargado':Select(attrs={'class':tailwind_class}),
        }
