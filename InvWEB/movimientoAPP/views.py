# En movimientoAPP/views.py
import json
from inventarioAPP.models import Producto
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from .models import Movimiento, StockActual
from .forms import MovimientoForm # ¡Usamos el formulario correcto!
from django.contrib import messages
from django.forms import ValidationError
from departamentoAPP.models import Departamento
# --- VISTAS DE MOVIMIENTO ---

class StockGroupedListview(ListView):
    """
    Esta vista agrupa el stock por departamento.
    """
    model = Departamento # ¡Cambiamos el modelo base!
    template_name = 'stock/list_grouped.html' # Nueva plantilla
    context_object_name = 'departamentos'
    
    def get_queryset(self):
        # Obtenemos todos los departamentos y precargamos
        # su encargado y sus items de stock (con el producto)
        # para evitar N+1 queries en la plantilla.
        return Departamento.objects.filter(activo=True).prefetch_related(
            'encargado', 
            'stock_items__producto' # 'stock_items' es el related_name
        )
    

class MovimientoListview(ListView):
    model = Movimiento
    template_name = 'movimiento/list.html'
    context_object_name = 'movimientos' # 'movimientos' es más plural
    paginate_by = 25 # Buena práctica

class MovimientoCreateView(CreateView):
    model = Movimiento
    template_name = 'movimiento/form.html'
    form_class = MovimientoForm
    success_url = reverse_lazy('movimientoAPP:movimiento_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ¡NUEVO! Pasamos los datos de productos al template como JSON
        productos_data = {
            str(p.id): str(p.unidad_medida)
            for p in Producto.objects.filter(activo=True)
        }
        context['productos_data_json'] = json.dumps(productos_data)
        
        return context
    
    def form_valid(self, form):
        """
        Aquí está la magia.
        Intentamos guardar, pero si el modelo (models.py) lanza un
        ValueError (ej. "No hay stock"), lo capturamos y lo
        mostramos como un error en el formulario, sin crashear.
        """
        try:
            # El form.save() disparará el método .save() de tu modelo
            return super().form_valid(form)
        except ValueError as e:
            # Añade el error (ej. "No hay stock...") al formulario
            form.add_error(None, str(e))
            return self.form_invalid(form)

class MovimientoUpdateView(UpdateView):
    """
    OJO: Esta vista SÓLO debe usarse para editar 'observaciones'.
    La lógica en tu models.py ya previene que se edite el stock.
    """
    model = Movimiento
    template_name = 'movimiento/form.html'
    # Solo permitimos editar la observación
    fields = ['observaciones'] 
    success_url = reverse_lazy('movimientoAPP:movimiento_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit_mode'] = True # Para deshabilitar campos en el template
        return context

# NO SE DEBE BORRAR UN MOVIMIENTO
# Borrar un movimiento desincroniza el stock.
# La forma correcta de "cancelar" un movimiento es crear
# un movimiento de ajuste (ej. una 'SALIDA' para anular una 'ENTRADA').
# Por eso, NO incluimos una MovimientoDeleteView.


# --- VISTA DE STOCK (SOLO LECTURA) ---

class StockListview(ListView):
    model = StockActual
    template_name = 'stock/list.html'
    context_object_name = 'stockactual'
    
    def get_queryset(self):
        # Mostramos solo los items que SÍ tienen stock
        return StockActual.objects.filter(cantidad__gt=0).select_related(
            'producto', 
            'departamento'
        )

# NO MÁS VISTAS PARA STOCK. 
# StockCreateView, StockUpdateView y StockDeleteView DEBEN SER ELIMINADAS.