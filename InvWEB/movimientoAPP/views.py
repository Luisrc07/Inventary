# En movimientoAPP/views.py
import json
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse # ¡HttpResponse añadido!
from django.db.models import Q # ¡Importante para filtros!
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

# --- Importaciones de Modelos ---
from .models import Movimiento, StockActual
from inventarioAPP.models import Producto
from departamentoAPP.models import Departamento

# --- Importaciones de Formularios ---
from .forms import MovimientoForm

# --- ¡IMPORTACIONES CLAVE DE PERMISOS! ---
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# --- Importaciones para PDF ---
from weasyprint import HTML

# =========================================================================
# VISTAS DE STOCK (CON PERMISOS)
# =========================================================================


@method_decorator(never_cache, name='dispatch')
class StockGroupedListview(LoginRequiredMixin, ListView):
    """
    Esta vista agrupa el stock por departamento.
    """
    model = Departamento 
    template_name = 'stock/list_grouped.html' 
    context_object_name = 'departamentos'
    
    def get_queryset(self):
        perfil = self.request.user.perfil
        
        # Preparamos el queryset base
        base_qs = Departamento.objects.filter(activo=True).prefetch_related(
            
            # --- ¡AQUÍ ESTÁ LA CORRECCIÓN! ---
            # Borramos 'encargado', que ya no existe.
            # Añadimos 'perfiles__user' (el related_name que creamos en usuario/models.py)
            'perfiles__user', 
            # --- FIN DE LA CORRECCIÓN ---
            
            'stock_items__producto' # 'stock_items' es el related_name
        )
        
        if perfil.es_admin:
            return base_qs # Admin ve todo
        
        # Gerente/Operador ve solo su departamento
        return base_qs.filter(pk=perfil.departamento.pk)
    
@method_decorator(never_cache, name='dispatch')
class StockListview(LoginRequiredMixin, ListView):
    """
    Vista de lista de stock individual.
    - Admin: Ve todo el stock.
    - Gerente/Operador: Ve SOLO el stock de su departamento.
    """
    model = StockActual
    template_name = 'stock/list.html'
    context_object_name = 'stockactual'
    
    def get_queryset(self):
        perfil = self.request.user.perfil
        
        # Preparamos el queryset base
        base_qs = StockActual.objects.filter(cantidad__gt=0).select_related(
            'perfiles__user',
            'stock_items__producto'
        )
        
        if perfil.es_admin:
            return base_qs # Admin ve todo
            
        # Gerente/Operador ve solo el stock de su departamento
        return base_qs.filter(departamento=perfil.departamento)

# =========================================================================
# VISTAS DE MOVIMIENTO (CON PERMISOS)
# =========================================================================

@method_decorator(never_cache, name='dispatch')
class MovimientoListview(LoginRequiredMixin, ListView):
    """
    Vista de lista de movimientos.
    - Admin: Ve todos los movimientos.
    - Gerente/Operador: Ve SOLO los movimientos de SU departamento.
    - ¡AHORA CON FILTROS!
    """
    model = Movimiento
    template_name = 'movimiento/list.html'
    context_object_name = 'movimientos'
    paginate_by = 10

    def get_queryset(self):
        perfil = self.request.user.perfil
        
        # 1. Obtener el queryset base según los permisos
        if perfil.es_admin:
            base_qs = Movimiento.objects.all().select_related(
                'producto', 'departamento_origen', 'departamento_destino'
            )
        else:
            depto_usuario = perfil.departamento
            base_qs = Movimiento.objects.filter(
                Q(departamento_origen=depto_usuario) | Q(departamento_destino=depto_usuario)
            ).select_related('producto', 'departamento_origen', 'departamento_destino')

        # 2. Obtener los parámetros de filtro del request GET
        fecha_inicio = self.request.GET.get('fecha_inicio')
        fecha_fin = self.request.GET.get('fecha_fin')
        departamento_id = self.request.GET.get('departamento_id')

        # 3. Aplicar los filtros al queryset base
        if fecha_inicio:
            # Filtra por fecha (incluyendo el día de inicio)
            base_qs = base_qs.filter(fecha__date__gte=fecha_inicio)
        
        if fecha_fin:
            # Filtra por fecha (incluyendo el día de fin)
            base_qs = base_qs.filter(fecha__date__lte=fecha_fin)
        
        if departamento_id:
            # Filtra por movimientos DONDE el departamento sea origen O destino
            base_qs = base_qs.filter(
                Q(departamento_origen_id=departamento_id) | Q(departamento_destino_id=departamento_id)
            )
            
        # Retorna el queryset filtrado y ordenado
        # (El 'ordering' en el Meta del modelo se encarga de ordenar por fecha)
        return base_qs

    def get_context_data(self, **kwargs):
        """
        Pasamos el perfil y los datos del filtro a la plantilla.
        """
        context = super().get_context_data(**kwargs)
        context['perfil'] = self.request.user.perfil
        
        # --- ¡NUEVO! Pasar datos para el formulario de filtro ---
        
        # 1. Pasar la lista de todos los departamentos activos para el <select>
        context['departamentos_list'] = Departamento.objects.filter(activo=True).order_by('nombre')
        
        # 2. Pasar los valores actuales del filtro para "recordarlos" en el form
        context['fecha_inicio'] = self.request.GET.get('fecha_inicio', '')
        context['fecha_fin'] = self.request.GET.get('fecha_fin', '')
        context['departamento_id'] = self.request.GET.get('departamento_id', '')

        return context
@method_decorator(never_cache, name='dispatch')
class MovimientoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Vista para crear un movimiento.
    - PERMITIDO: Admin, Gerente.
    - DENEGADO: Operador.
    """
    model = Movimiento
    template_name = 'movimiento/form.html'
    form_class = MovimientoForm
    success_url = reverse_lazy('movimientoAPP:movimiento_list')

    def test_func(self):
        """
        Prueba de permiso: Solo Admins o Gerentes pueden crear.
        """
        perfil = self.request.user.perfil
        return perfil.es_admin or perfil.es_gerente

    def get_form_kwargs(self):
        """
        Enviamos el 'user' actual al __init__ del formulario.
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        productos_data = {
            str(p.id): str(p.unidad_medida)
            for p in Producto.objects.filter(activo=True) # Filtraremos por JS, traemos todos
        }
        context['productos_data_json'] = json.dumps(productos_data)

        user_depto_pk = None
        if hasattr(self.request.user, 'perfil') and self.request.user.perfil.departamento:
            user_depto_pk = self.request.user.perfil.departamento.pk
            
        context['user_depto_pk'] = user_depto_pk
        context['is_admin'] = self.request.user.perfil.es_admin
        
        return context
    
    def form_valid(self, form):
        """
        Capturamos el ValueError del modelo (ej. "No hay stock").
        """
        form.instance.usuario_registra = self.request.user
        
        tipo = form.cleaned_data.get('tipo')
        
        # 2. Solo calculamos en ENTRADAS
        if tipo == 'ENTRADA':
            producto = form.cleaned_data.get('producto')
            costo_bs = form.cleaned_data.get('costo_unitario_bs') # Costo por PAQUETE
            tasa = form.cleaned_data.get('tasa_cambio')
            
            if (producto and producto.unidad_medida and producto.unidad_medida > 0 
                and costo_bs and costo_bs > 0 and tasa and tasa > 0):
                
                # a. Costo del paquete en USD
                costo_paquete_usd = costo_bs / tasa
                
                # b. Costo por UNIDAD (tu petición)
                costo_unidad_usd = costo_paquete_usd / producto.unidad_medida
                
                # c. Guarda el valor en el nuevo campo del modelo
                form.instance.costo_unitario_usd = costo_unidad_usd
            else:
                # Si falta algún dato, guarda NULL
                form.instance.costo_unitario_usd = None
        else:
            # Si no es ENTRADA, no hay costo
            form.instance.costo_unitario_usd = None
        try:
            return super().form_valid(form)
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        
@method_decorator(never_cache, name='dispatch')
class MovimientoUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista para editar SÓLO observaciones.
    """
    model = Movimiento
    template_name = 'movimiento/form.html'
    fields = ['observaciones'] 
    success_url = reverse_lazy('movimientoAPP:movimiento_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit_mode'] = True
        return context

# =========================================================================
# VISTA DE REPORTE PDF (CON PERMISOS)
# =========================================================================

def generar_reporte_stock_pdf(request, pk):
    """
    Genera un reporte PDF del stock para un departamento.
    - Admin: Puede ver el reporte de CUALQUIER departamento.
    - Gerente/Operador: Solo puede ver el reporte de SU departamento.
    """
    # 1. Obtener el departamento
    depto = get_object_or_404(
        Departamento.objects.prefetch_related(
            'perfiles__user', 
            'stock_items__producto'
        ), 
        pk=pk
    )

    # 2. ¡CHEQUEO DE PERMISOS!
    perfil = request.user.perfil
    if not perfil.es_admin and perfil.departamento != depto:
        return HttpResponse("Permiso Denegado. Solo puede ver reportes de su propio departamento.", status=403)

    # 3. Filtrar stock y contexto (como ya lo tenías)
    stock_items = [
        item for item in depto.stock_items.all() if item.cantidad > 0
    ]
    context = {
        'depto': depto,
        'stock_items': stock_items,
        'fecha_actual': timezone.now(), 
    }
    
    # 4. Renderizar HTML
    html_string = render_to_string('stock/reporte_pdf_template.html', context)
    
    # 5. Generar PDF
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()

    # 6. Devolver respuesta
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="reporte_stock_{depto.nombre}.pdf"'
    return response

# =========================================================================
# VISTA AJAX (SIN CAMBIOS)
# =========================================================================

def load_productos(request):
    """
    Carga productos para el select dinámico. No necesita permisos.
    """
    categoria_id = request.GET.get('categoria_id')
    
    if categoria_id:
        # Asumiendo que tu modelo Producto SÍ tiene 'categoria_id'
        productos = Producto.objects.filter(categoria_id=categoria_id).order_by('nombre')
    else:
        productos = Producto.objects.none()
        
    productos_list = []
    for producto in productos:
        productos_list.append({
            'id': str(producto.pk), 
            'nombre': f"{producto.nombre} ({producto.unidad_medida} u/paq)" 
        })
        
    return JsonResponse(productos_list, safe=False)