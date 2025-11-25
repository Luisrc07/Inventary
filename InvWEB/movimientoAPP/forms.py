# -------------------------------------------------------------------------
# forms.py (Copia y reemplaza todo el contenido)
# -------------------------------------------------------------------------
from django import forms
from django.forms import formset_factory
from .models import Movimiento, Departamento
from inventarioAPP.models import Producto, Categoria
from proveedorAPP.models import Proveedor
from django.forms import (
    TextInput, Textarea, Select, NumberInput, ModelChoiceField
)

tailwind_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'

class CategoriaModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.nombre
    
# --- FORMULARIO ORIGINAL (Para Edición Simple) ---
class MovimientoForm(forms.ModelForm):
    categoria_select = CategoriaModelChoiceField(
        queryset=Categoria.objects.none(),
        label="Filtrar por Categoría",
        required=False,
        widget=Select(attrs={'class': tailwind_class})
    )
    class Meta:
        model = Movimiento
        fields = ['observaciones']
        widgets = {
            'observaciones': Textarea(attrs={'class': tailwind_class, 'rows': 3}),
        }

# ==============================================================================
# NUEVOS FORMULARIOS PARA CARGA MÚLTIPLE
# ==============================================================================

class MovimientoCabeceraForm(forms.Form):
    tipo = forms.ChoiceField(
        choices=Movimiento.TIPO_CHOICES, 
        widget=Select(attrs={'class': tailwind_class, 'id': 'id_tipo'})
    )
    
    departamento_origen = forms.ModelChoiceField(
        queryset=Departamento.objects.filter(activo=True), 
        required=False, 
        widget=Select(attrs={'class': tailwind_class, 'id': 'id_departamento_origen'})
    )
    
    departamento_destino = forms.ModelChoiceField(
        queryset=Departamento.objects.filter(activo=True), 
        required=False, 
        widget=Select(attrs={'class': tailwind_class, 'id': 'id_departamento_destino'})
    )
    
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.all(), 
        required=False, 
        widget=Select(attrs={'class': tailwind_class})
    )
    
    numero_factura = forms.CharField(
        required=False, 
        label="N° Factura/Ref",
        widget=TextInput(attrs={'class': tailwind_class})
    )
    
    tasa_cambio = forms.DecimalField(
        required=False, 
        min_value=0.01, 
        label="Tasa (Bs./USD)",
        widget=NumberInput(attrs={'class': tailwind_class, 'step': '0.0001'})
    )
    
    observaciones = forms.CharField(
        widget=Textarea(attrs={'class': tailwind_class, 'rows': 2}), 
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) # Guardamos el usuario para usarlo en clean()
        super().__init__(*args, **kwargs)
        
        # Filtro de ORIGEN: Si no es admin, solo puede sacar de su depto.
        if self.user and hasattr(self.user, 'perfil') and not self.user.perfil.es_admin:
            depto_usuario = self.user.perfil.departamento
            if depto_usuario:
                self.fields['departamento_origen'].queryset = Departamento.objects.filter(pk=depto_usuario.pk)
                self.fields['departamento_origen'].initial = depto_usuario
        
        # NOTA: No filtramos DESTINO aquí, porque en Transferencias sí necesita ver otros deptos.
        # La restricción de ENTRADA se hace en clean().

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        
        # Obtenemos perfil del usuario
        es_admin = False
        depto_usuario = None
        if self.user and hasattr(self.user, 'perfil'):
            es_admin = self.user.perfil.es_admin
            depto_usuario = self.user.perfil.departamento

        # --- VALIDACIONES POR TIPO ---
        if tipo == 'SALIDA':
            if not cleaned_data.get('departamento_origen'):
                self.add_error('departamento_origen', 'Para una SALIDA, seleccione el Origen.')
                
        elif tipo == 'ENTRADA':
            # === AQUÍ ESTÁ LA MAGIA PARA RESTRINGIR ENTRADAS ===
            if not es_admin and depto_usuario:
                # Si no es admin, el destino ES OBLIGATORIAMENTE su departamento
                cleaned_data['departamento_destino'] = depto_usuario
            else:
                # Si es admin, debe haber seleccionado uno
                if not cleaned_data.get('departamento_destino'):
                    self.add_error('departamento_destino', 'Seleccione el Destino.')

            if not cleaned_data.get('proveedor'):
                self.add_error('proveedor', 'Seleccione un Proveedor.')
            if not cleaned_data.get('numero_factura'):
                self.add_error('numero_factura', 'Indique el N° de Factura.')
            if not cleaned_data.get('tasa_cambio'):
                self.add_error('tasa_cambio', 'Indique la Tasa de Cambio.')
                
        elif tipo == 'TRANSFERENCIA':
            origen = cleaned_data.get('departamento_origen')
            destino = cleaned_data.get('departamento_destino')
            if not origen:
                self.add_error('departamento_origen', 'Seleccione Origen.')
            if not destino:
                self.add_error('departamento_destino', 'Seleccione Destino.')
            if origen and destino and origen == destino:
                self.add_error('departamento_destino', 'El origen y destino no pueden ser iguales.')
        
        return cleaned_data

class MovimientoDetalleForm(forms.Form):
    categoria_temp = forms.ModelChoiceField(
        queryset=Categoria.objects.all(), required=False, empty_label="--- Categoría ---",
        widget=Select(attrs={'class': 'w-full border-gray-300 rounded focus:ring-indigo-500 item-categoria text-sm'})
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True), 
        widget=Select(attrs={'class': 'w-full border-gray-300 rounded focus:ring-indigo-500 item-producto text-sm'})
    )
    cantidad = forms.DecimalField(
        min_value=0.01, widget=NumberInput(attrs={'class': 'w-full border-gray-300 rounded focus:ring-indigo-500 item-cantidad text-sm', 'placeholder': 'Cant. Paq', 'step': '0.01'})
    )
    costo_unitario_bs = forms.DecimalField(
        required=False, min_value=0, widget=NumberInput(attrs={'class': 'w-full border-gray-300 rounded focus:ring-indigo-500 item-costo text-sm', 'placeholder': 'Bs.', 'step': '0.01'})
    )

MovimientoFormSet = formset_factory(MovimientoDetalleForm, extra=1)