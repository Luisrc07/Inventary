
from django import forms
from .models import Movimiento, Departamento
from inventarioAPP.models import Producto, Categoria
from django.forms import TextInput, Textarea, Select, NumberInput
from django.forms import ModelChoiceField
from django.forms import Select


tailwind_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'

class CategoriaModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.nombre
    
class MovimientoForm(forms.ModelForm):
    # 1. Campo de Categoría (Auxiliar)
    categoria_select = CategoriaModelChoiceField(
        queryset=Categoria.objects.all(),
        label="Filtrar por Categoría",
        required=False,
        empty_label="--- Seleccione una Categoría ---",
        # Asignamos el ID esperado por el JS
        widget=Select(attrs={'class': tailwind_class, 'id': 'select-categoria'})
    )

    class Meta:
        model = Movimiento
        # Seleccionamos los campos que el usuario DEBE llenar
        fields = [
            'tipo',
            'producto',
            'cantidad',
            'numero_factura', 
            'costo_unitario_bs', 
            'tasa_cambio', 
            'proveedor',
            'departamento_origen',
            'departamento_destino',
            'observaciones',
        ]
        widgets = {
            'tipo': Select(attrs={'class': tailwind_class, 'id': 'id_tipo'}),
            'producto': Select(attrs={'class': tailwind_class, 'id': 'select-producto'}),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 2. Inicializar el campo 'producto' vacío
        self.fields['producto'].queryset = Producto.objects.none()
        
        # Identificador para la categoría a usar en el filtrado
        categoria_id_a_filtrar = None
        
        # --- Lógica de Repoblación del Select 'producto' ---
        
        # Caso A: Edición de un objeto existente (Instancia con producto_id)
        if self.instance and self.instance.pk and self.instance.producto_id:
            # Producto existe, podemos obtener su categoría
            producto_instance = self.instance.producto 
            categoria_id_a_filtrar = producto_instance.categoria_id
            
        # Caso B: POST fallido (el formulario contiene datos)
        elif self.data and self.data.get('categoria_select'):
            # Si el usuario seleccionó una categoría en el intento fallido, la usamos
            categoria_id_a_filtrar = self.data.get('categoria_select')
        
        
        # Si logramos identificar la categoría, filtramos el queryset
        if categoria_id_a_filtrar:
            # Filtramos el queryset del producto por la categoría
            self.fields['producto'].queryset = Producto.objects.filter(
                categoria_id=categoria_id_a_filtrar
            ).order_by('nombre')
            
            # Establecemos la categoría inicial en el campo auxiliar (para que se muestre seleccionada)
            self.initial['categoria_select'] = categoria_id_a_filtrar
        
        # --- Fin Lógica de Repoblación ---


        # 1. Filtrar los campos de Departamento (Mantenido)
        self.fields['departamento_origen'].queryset = Departamento.objects.filter(activo=True)
        self.fields['departamento_destino'].queryset = Departamento.objects.filter(activo=True)


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
