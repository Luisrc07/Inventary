from django import forms 
from inventarioAPP.models import Categoria, Producto
from django.forms import TextInput, Textarea, Select, NumberInput, EmailInput

tailwind_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'



class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre','descripcion']
        widgets= {
            'nombre': TextInput(attrs={'class': tailwind_class}),
            'descripcion': Textarea(attrs={'class': tailwind_class}),
        }

class ProductoForm(forms.ModelForm):
    class Meta:
        model= Producto
        fields= ['nombre','sku','categoria','descripcion','unidad_medida']
        widgets= {
            'nombre': TextInput(attrs={'class': tailwind_class}),
            'sku': TextInput(attrs={'class': tailwind_class}),
            'categoria': Select(attrs={'class': tailwind_class}),
            'descripcion': Textarea(attrs={'class': tailwind_class}),'unidad_medida': NumberInput(attrs={'class': tailwind_class}),
        }