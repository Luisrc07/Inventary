from django import forms 
from proveedorAPP.models import Proveedor
from django.forms import TextInput, Textarea, Select, NumberInput, EmailInput

tailwind_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'



class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre','rif','telefono','email','direccion', 'activo']
        widgets= {
            'nombre': TextInput(attrs={'class': tailwind_class, 'required': 'True'}),
            'rif': TextInput(attrs={'class': tailwind_class, 'required': 'True'}),
            'telefono': TextInput(attrs={'class': tailwind_class, 'required': 'True'}),
            'email': EmailInput(attrs={'class': tailwind_class}),
            'direccion': Textarea(attrs={'class': tailwind_class, 'rows':2}),
        }
