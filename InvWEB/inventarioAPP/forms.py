# Copyright (c) 2025, Luis Rodriguez.
# (y el resto de tu aviso de licencia)
# -------------------
from django import forms
from inventarioAPP.models import Categoria, Producto
from django.forms import (
    TextInput, Textarea, Select, NumberInput, CheckboxInput
)

# Estilo de Tailwind que usas
tailwind_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'
tailwind_checkbox = 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre','descripcion']
        widgets= {
            'nombre': TextInput(attrs={'class': tailwind_class}),
            'descripcion': Textarea(attrs={'class': tailwind_class, 'rows':2}),
        }

# =========================================================================
# FORMULARIO DE PRODUCTO (CORREGIDO)
# =========================================================================
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        
        # --- ¡CORRECCIÓN 1: Añadir campos a la lista! ---
        fields = [
            'nombre', 
            'sku', 
            'categoria', 
            'descripcion', 
            'unidad_medida', 
            'stock_minimo', # <-- AÑADIDO
            'activo'        # <-- AÑADIDO
        ]
        
        # --- ¡CORRECCIÓN 2: Añadir widgets para los campos nuevos! ---
        widgets = {
            'nombre': TextInput(attrs={'class': tailwind_class}),
            'sku': TextInput(attrs={'class': tailwind_class, 'Style':'text-transform : uppercase ;'}),
            'categoria': Select(attrs={'class': tailwind_class}),
            'descripcion': Textarea(attrs={'class': tailwind_class, 'rows':2}),
            'unidad_medida': NumberInput(attrs={'class': tailwind_class, 'step': 'any', 'min': '0.01'}),
            
            # --- Widgets para los campos nuevos ---
            'stock_minimo': NumberInput(attrs={'class': tailwind_class, 'min': '0', 'step': 'any', 'value': '5.0'}),
            'activo': CheckboxInput(attrs={'class': tailwind_checkbox, 'style': 'margin-top: 1px;'}),
        }

        # --- CORRECCIÓN 3: Añadir etiquetas y ayuda para mejor UI ---
        labels = {
            'sku': 'SKU (Código de Producto)',
            'unidad_medida': 'Unidades por Paquete (Ej: 100)',
            'stock_minimo': 'Stock Mínimo (en Paquetes)',
            'activo': 'Producto Activo'
        }
        help_texts = {
            'stock_minimo': 'Cantidad mínima de PAQUETES antes de generar una alerta en el dashboard.'
        }

    def clean_sku(self):
        sku_value = self.cleaned_data.get('sku')
        if sku_value:
            return sku_value.upper()
        return sku_value