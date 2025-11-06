# En movimientoAPP/forms.py
from django import forms
from .models import Movimiento, Departamento
from inventarioAPP.models import Producto, Categoria
from django.forms import (
    TextInput, Textarea, Select, NumberInput, ModelChoiceField
)

# Estilo de Tailwind
tailwind_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'

class CategoriaModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.nombre
    
class MovimientoForm(forms.ModelForm):
    # Campo auxiliar de Categoría
    categoria_select = CategoriaModelChoiceField(
        queryset=Categoria.objects.none(),
        label="Filtrar por Categoría",
        required=False,
        empty_label="--- Seleccione una Categoría ---",
        widget=Select(attrs={'class': tailwind_class, 'id': 'select-categoria'})
    )

    class Meta:
        model = Movimiento
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
            'cantidad': NumberInput(attrs={'class': tailwind_class, 'min': '0.01', 'step': 'any'}), 
            'numero_factura': TextInput(attrs={'class': tailwind_class}), 
            'costo_unitario_bs': NumberInput(attrs={'class': tailwind_class, 'step': 'any', 'min': '0.01'}), 
            'tasa_cambio': NumberInput(attrs={'class': tailwind_class, 'step': 'any', 'min': '0.01'}),
            'proveedor': Select(attrs={'class': tailwind_class}), 
            'departamento_origen': Select(attrs={'class': tailwind_class}), 
            'departamento_destino': Select(attrs={'class': tailwind_class}), 
            'observaciones': Textarea(attrs={'class': tailwind_class, 'rows': 3}),
        }
        labels = {
            'cantidad': 'Cantidad de Paquetes (Ej: Cajas, Bolsas, etc.)'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        
        super().__init__(*args, **kwargs)
        
        self.fields['producto'].queryset = Producto.objects.none()
        self.fields['categoria_select'].queryset = Categoria.objects.none()

        categoria_id_a_filtrar = None
        
        if self.instance and self.instance.pk and self.instance.producto_id:
            producto_instance = self.instance.producto 
            categoria_id_a_filtrar = producto_instance.categoria_id
            
            self.fields['categoria_select'].queryset = Categoria.objects.all().order_by('nombre')
            self.fields['producto'].queryset = Producto.objects.filter(
                categoria_id=categoria_id_a_filtrar
            ).order_by('nombre')
            
            self.initial['categoria_select'] = categoria_id_a_filtrar

        elif self.data:
            self.fields['categoria_select'].queryset = Categoria.objects.all().order_by('nombre')
            
            categoria_id_a_filtrar = self.data.get('categoria_select')
            if categoria_id_a_filtrar:
                self.fields['producto'].queryset = Producto.objects.filter(
                    categoria_id=categoria_id_a_filtrar
                ).order_by('nombre')
        
        queryset_departamentos = Departamento.objects.filter(activo=True)
        self.fields['departamento_origen'].queryset = queryset_departamentos
        self.fields['departamento_destino'].queryset = queryset_departamentos

        if self.user and hasattr(self.user, 'perfil') and not self.user.perfil.es_admin:
            depto_usuario = self.user.perfil.departamento
            if depto_usuario:
                self.fields['departamento_origen'].queryset = Departamento.objects.filter(pk=depto_usuario.pk)

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        
        if self.user and hasattr(self.user, 'perfil') and not self.user.perfil.es_admin:
            depto_usuario = self.user.perfil.departamento
            
            if tipo == 'TRANSFERENCIA':
                self.fields['departamento_destino'].queryset = Departamento.objects.filter(activo=True)
                destino_transferencia = cleaned_data.get('departamento_destino')
                if destino_transferencia == depto_usuario:
                    self.add_error('departamento_destino', 'No puede transferir stock a su mismo departamento.')
            
            if tipo == 'ENTRADA':
                if cleaned_data.get('departamento_destino') != depto_usuario:
                    self.add_error('departamento_destino', 'Solo puede registrar ENTRADAS para su propio departamento.')
        
        costo_unitario_bs = cleaned_data.get('costo_unitario_bs')
        tasa_cambio = cleaned_data.get('tasa_cambio')
        
        if tipo == 'ENTRADA':
            if not cleaned_data.get('proveedor'):
                self.add_error('proveedor', 'Debe seleccionar un proveedor para las ENTRADAS.')
            if not cleaned_data.get('departamento_destino'):
                self.add_error('departamento_destino', 'Debe seleccionar un departamento de destino.')
            if not costo_unitario_bs or costo_unitario_bs <= 0:
                self.add_error('costo_unitario_bs', 'Debe ingresar el costo unitario (Bs.).')
            if not tasa_cambio or tasa_cambio <= 0:
                self.add_error('tasa_cambio', 'Debe ingresar la tasa de cambio (Bs./USD).')
            if not cleaned_data.get('numero_factura'):
                self.add_error('numero_factura', 'Debe ingresar el N° de factura/referencia.')
            cleaned_data['departamento_origen'] = None
            
        elif tipo == 'SALIDA':
            if not cleaned_data.get('departamento_origen'):
                self.add_error('departamento_origen', 'Debe seleccionar un departamento de origen.')
            cleaned_data['proveedor'] = None
            cleaned_data['departamento_destino'] = None
            cleaned_data['costo_unitario_bs'] = None
            cleaned_data['tasa_cambio'] = None
            cleaned_data['numero_factura'] = None
            
        elif tipo == 'TRANSFERENCIA':
            if not cleaned_data.get('departamento_origen'):
                self.add_error('departamento_origen', 'Debe seleccionar un departamento de origen.')
            if not cleaned_data.get('departamento_destino'):
                self.add_error('departamento_destino', 'Debe seleccionar un departamento de destino.')
            
            if cleaned_data.get('departamento_origen') == cleaned_data.get('departamento_destino'):
                self.add_error('departamento_destino', 'El origen y el destino no pueden ser el mismo departamento.')
                
            cleaned_data['proveedor'] = None
            cleaned_data['costo_unitario_bs'] = None
            cleaned_data['tasa_cambio'] = None
            cleaned_data['numero_factura'] = None
        
        return cleaned_data