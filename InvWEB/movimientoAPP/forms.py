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
            'numero_factura',      # <-- ¡NUEVO CAMPO!
            'costo_unitario_bs',   # <-- ¡NUEVO CAMPO!
            'tasa_cambio',         # <-- ¡NUEVO CAMPO!
            'proveedor',
            'departamento_origen',
            'departamento_destino',
            'observaciones',
        ]
        widgets = {
            'tipo': Select(attrs={'class': tailwind_class, 'id': 'id_tipo'}),
            'producto': Select(attrs={'class': tailwind_class}),
            # *** CAMBIO AQUÍ: 'step': 'any' para aceptar decimales ***

            'cantidad': NumberInput(attrs={'class': tailwind_class, 'min': '0.01', 'step': 'any'}), 
            'numero_factura': TextInput(attrs={'class': tailwind_class}), 
            'costo_unitario_bs': NumberInput(attrs={'class': tailwind_class, 'step': 'any', 'min': '0.01'}), 
            'tasa_cambio': NumberInput(attrs={'class': tailwind_class, 'step': 'any', 'min': '0.01'}),

            
            # Ya no asignamos IDs a los Selects, dejamos que Django lo haga y usamos el wrapper
            'proveedor': Select(attrs={'class': tailwind_class}), 
            'departamento_origen': Select(attrs={'class': tailwind_class}), 
            'departamento_destino': Select(attrs={'class': tailwind_class}), 
            'observaciones': Textarea(attrs={'class': tailwind_class, 'rows': 3}),
        }
        labels = {
            'cantidad': 'Cantidad de Paquetes (Ej: Cajas, Bolsas, etc.)'
        }

    #def __init__(self, *args, **kwargs):
        #super().__init__(*args, **kwargs)
        # Ocultamos el campo real de origen por defecto
        #self.fields['departamento_origen'].widget.attrs['style'] = 'display: none;'


    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        costo_unitario_bs = cleaned_data.get('costo_unitario_bs')
        tasa_cambio = cleaned_data.get('tasa_cambio')
        
        if tipo == 'ENTRADA':
            if not cleaned_data.get('proveedor'):
                self.add_error('proveedor', 'Debe seleccionar un proveedor para las ENTRADAS.')
            if not cleaned_data.get('departamento_destino'):
                self.add_error('departamento_destino', 'Debe seleccionar un departamento de destino.')
                
            # Validaciones de Costo
            if not costo_unitario_bs or costo_unitario_bs <= 0:
                self.add_error('costo_unitario_bs', 'Debe ingresar el costo unitario del paquete en Bolívares.')
            if not tasa_cambio or tasa_cambio <= 0:
                self.add_error('tasa_cambio', 'Debe ingresar la tasa de cambio vigente (Bs./USD).')
            
            # El campo numero_factura debería ser obligatorio para ENTRADA
            if not cleaned_data.get('numero_factura'):
                self.add_error('numero_factura', 'Debe ingresar el número de factura o referencia para la ENTRADA.')
                
            # Aseguramos que los campos de origen/destino nulos de ENTRADA no den error en el modelo
            cleaned_data['departamento_origen'] = None
            
        elif tipo == 'SALIDA':
            # ... (Tus validaciones para SALIDA) ...
            cleaned_data['proveedor'] = None
            cleaned_data['departamento_destino'] = None
            cleaned_data['costo_unitario_bs'] = None
            cleaned_data['tasa_cambio'] = None
            cleaned_data['numero_factura'] = None
            
        elif tipo == 'TRANSFERENCIA':
            # ... (Tus validaciones para TRANSFERENCIA) ...
            cleaned_data['proveedor'] = None
            cleaned_data['costo_unitario_bs'] = None
            cleaned_data['tasa_cambio'] = None
            cleaned_data['numero_factura'] = None
        
        return cleaned_data