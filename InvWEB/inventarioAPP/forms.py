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
            'nombre': TextInput(attrs={'class': tailwind_class, 'required': 'True'}),
            'sku': TextInput(attrs={'class': tailwind_class,'required': 'True', 'style': 'text-transform: uppercase;'}),
            'categoria': Select(attrs={'class': tailwind_class, 'required': 'True'}),
            'descripcion': Textarea(attrs={'class': tailwind_class, }),
            'unidad_medida': NumberInput(attrs={'class': tailwind_class, 'step': 'any', 'min': '0.01', 'required': 'True'}),
        }
    def clean_sku(self): 
        """
        Garantiza que el valor se convierta a mayúsculas antes de ser
        asignado a la instancia del modelo.
        """
        # 1. Obtiene el valor enviado por el usuario
        valor = self.cleaned_data.get('sku')
        
        # 2. Verifica que tenga un valor y lo convierte a mayúsculas
        if valor:
            return valor.upper()
        
        # 3. Retorna el valor (si es None o vacío, lo retorna como está)
        return valor

