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
from django.utils import timezone
from departamentoAPP.models import Departamento
# --- VISTAS DE MOVIMIENTO ---

# --- IMPORTACIONES PARA PDF! ---
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from weasyprint import HTML
# -------------------------------------

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

# --- VISTA PARA GENERAR PDF DE STOCK POR DEPARTAMENTO ---

def generar_reporte_stock_pdf(request, pk):
    """
    Genera un reporte en PDF del stock actual para un departamento específico.
    """
    from .models import StockActual # Importación local para evitar circular, o ponla arriba.
    from departamentoAPP.models import Departamento # Idem.

    # 1. Obtener el departamento y su stock (solo con cantidad > 0)
    try:
        depto = get_object_or_404(
            Departamento.objects.prefetch_related(
                'encargado', 
                'stock_items__producto'
            ), 
            pk=pk
        )
    except:
        # Nota: Django ya maneja el 404 si no encuentra por pk,
        # pero es bueno tener un bloque try/except si esperas más errores.
        return HttpResponse("Departamento no encontrado.", status=404)

    # Filtramos los items para solo mostrar los que tienen stock positivo
    stock_items = [
        item for item in depto.stock_items.all() if item.cantidad > 0
    ]

    # 2. Definir el contexto para la plantilla del PDF
    context = {
        'depto': depto,
        'stock_items': stock_items,
        'fecha_actual': timezone.now(), 
    }
    
    # 3. Renderizar la plantilla HTML a un string
    html_string = render_to_string('stock/reporte_pdf_template.html', context)

    # 4. Generar el PDF usando WeasyPrint
    # build_absolute_uri() es importante para que WeasyPrint pueda cargar cualquier CSS.
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()

    # 5. Devolver la respuesta HTTP con el PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="reporte_stock_{depto.nombre}.pdf"'
    
    return response