from django import forms 
from inventarioAPP.models import Categoria, Producto
from django.forms import TextInput, Textarea, Select, NumberInput, EmailInput

tailwind_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'



class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre','descripcion']
        widgets= {
            'nombre': TextInput(attrs={'class': tailwind_class}),
            'descripcion': Textarea(attrs={'class': tailwind_class, 'rows':2}),
        }

class StockForm(forms.ModelForm):
    class Meta:
        model= Producto
        fields= ['nombre','sku','categoria','descripcion','unidad_medida']
        widgets= {
            'nombre': TextInput(attrs={'class': tailwind_class, 'required': 'True'}),
            'sku': TextInput(attrs={'class': tailwind_class,'required': 'True', 'Style':'text-transform : uppercase ;'}),
            'categoria': Select(attrs={'class': tailwind_class, 'required': 'True'}),
            'descripcion': Textarea(attrs={'class': tailwind_class, 'rows':2}),
            'unidad_medida': NumberInput(attrs={'class': tailwind_class, 'step': 'any', 'min': '0.01', 'required': 'True'}),
        }
    def clean_sku(self):
        sku_value = self.cleaned_data.get('sku')

        if sku_value:
            return sku_value.upper()
    
        return sku_value