# En movimientoAPP/forms.py

from django import forms
from .models import Movimiento
from django.forms import TextInput, Textarea, Select, NumberInput

tailwind_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'

class MovimientoForm(forms.ModelForm):
    
    class Meta:
        model = Movimiento
        # Seleccionamos los campos que el usuario DEBE llenar
        fields = [
            'tipo',
            'producto',
            'cantidad',
            'proveedor',
            'departamento_origen',
            'departamento_destino',
            'observaciones',
        ]
        widgets = {
            'tipo': Select(attrs={'class': tailwind_class, 'id': 'id_tipo'}),
            'producto': Select(attrs={'class': tailwind_class}),
            'cantidad': NumberInput(attrs={'class': tailwind_class, 'min': '1'}),
            'proveedor': Select(attrs={'class': tailwind_class, 'id': 'id_proveedor_wrapper'}),
            'departamento_origen': Select(attrs={'class': tailwind_class, 'id': 'id_origen_wrapper'}),
            'departamento_destino': Select(attrs={'class': tailwind_class, 'id': 'id_destino_wrapper'}),
            'observaciones': Textarea(attrs={'class': tailwind_class, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        """
        Opcional pero recomendado:
        Filtra los queryset para que solo muestre, por ejemplo, productos activos.
        """
        super().__init__(*args, **kwargs)
        # Ejemplo:
        # self.fields['producto'].queryset = Producto.objects.filter(activo=True)
        # self.fields['departamento_origen'].queryset = Departamento.objects.filter(activo=True)
        # ...etc.

    def clean(self):
        """
        Validación extra que complementa la lógica del modelo.
        """
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        
        # Estas validaciones se hacen aquí Y en el modelo,
        # pero hacerlas aquí da feedback instantáneo al usuario.
        if tipo == 'ENTRADA':
            if not cleaned_data.get('proveedor'):
                self.add_error('proveedor', 'Debe seleccionar un proveedor para las ENTRADAS.')
            if not cleaned_data.get('departamento_destino'):
                self.add_error('departamento_destino', 'Debe seleccionar un departamento de destino.')
        
        elif tipo == 'SALIDA':
            if not cleaned_data.get('departamento_origen'):
                self.add_error('departamento_origen', 'Debe seleccionar un departamento de origen.')
        
        elif tipo == 'TRANSFERENCIA':
            if not cleaned_data.get('departamento_origen'):
                self.add_error('departamento_origen', 'Debe seleccionar un origen.')
            if not cleaned_data.get('departamento_destino'):
                self.add_error('departamento_destino', 'Debe seleccionar un destino.')
            if cleaned_data.get('departamento_origen') == cleaned_data.get('departamento_destino'):
                self.add_error(None, 'El origen y el destino no pueden ser el mismo departamento.')
        
        return cleaned_data