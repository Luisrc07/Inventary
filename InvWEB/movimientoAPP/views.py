# En movimientoAPP/views.py

import json
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse 
from django.db.models import Q 
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

# --- Importaciones de Modelos ---
from .models import Movimiento, StockActual
from inventarioAPP.models import Producto, Categoria 
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
    # ... (Sin cambios) ...
    model = Departamento 
    template_name = 'stock/list_grouped.html' 
    context_object_name = 'departamentos'
    
    def get_queryset(self):
        perfil = self.request.user.perfil
        
        base_qs = Departamento.objects.filter(activo=True).prefetch_related(
            'perfiles__user', 
            'stock_items__producto'
        )
        
        if perfil.es_admin:
            return base_qs 
        
        return base_qs.filter(pk=perfil.departamento.pk)
    
@method_decorator(never_cache, name='dispatch')
class StockListview(LoginRequiredMixin, ListView):
    # ... (Sin cambios aquí, la corrección anterior era correcta) ...
    model = StockActual
    template_name = 'stock/list.html'
    context_object_name = 'stockactual'
    
    def get_queryset(self):
        perfil = self.request.user.perfil
        
        base_qs = StockActual.objects.filter(cantidad__gt=0).select_related(
            'producto', 'departamento'
        )
        
        if perfil.es_admin:
            return base_qs 
            
        return base_qs.filter(departamento=perfil.departamento)

# =========================================================================
# VISTAS DE MOVIMIENTO (CON PERMISOS)
# =========================================================================

@method_decorator(never_cache, name='dispatch')
class MovimientoListview(LoginRequiredMixin, ListView):
    # ... (Sin cambios) ...
    model = Movimiento
    template_name = 'movimiento/list.html'
    context_object_name = 'movimientos'
    paginate_by = 10

    def get_queryset(self):
        perfil = self.request.user.perfil
        
        if perfil.es_admin:
            base_qs = Movimiento.objects.all().select_related(
                'producto', 'departamento_origen', 'departamento_destino'
            )
        else:
            depto_usuario = perfil.departamento
            base_qs = Movimiento.objects.filter(
                Q(departamento_origen=depto_usuario) | Q(departamento_destino=depto_usuario)
            ).select_related('producto', 'departamento_origen', 'departamento_destino')

        fecha_inicio = self.request.GET.get('fecha_inicio')
        fecha_fin = self.request.GET.get('fecha_fin')
        departamento_id = self.request.GET.get('departamento_id')

        if fecha_inicio:
            base_qs = base_qs.filter(fecha__date__gte=fecha_inicio)
        if fecha_fin:
            base_qs = base_qs.filter(fecha__date__lte=fecha_fin)
        if departamento_id:
            base_qs = base_qs.filter(
                Q(departamento_origen_id=departamento_id) | Q(departamento_destino_id=departamento_id)
            )
        return base_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['perfil'] = self.request.user.perfil
        context['departamentos_list'] = Departamento.objects.filter(activo=True).order_by('nombre')
        context['fecha_inicio'] = self.request.GET.get('fecha_inicio', '')
        context['fecha_fin'] = self.request.GET.get('fecha_fin', '')
        context['departamento_id'] = self.request.GET.get('departamento_id', '')
        return context

@method_decorator(never_cache, name='dispatch')
class MovimientoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    # ... (Sin cambios) ...
    model = Movimiento
    template_name = 'movimiento/form.html'
    form_class = MovimientoForm
    success_url = reverse_lazy('movimientoAPP:movimiento_list')

    def test_func(self):
        perfil = self.request.user.perfil
        return perfil.es_admin or perfil.es_gerente

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        productos_data = {
            str(p.id): str(p.unidad_medida)
            for p in Producto.objects.filter(activo=True)
        }
        context['productos_data_json'] = json.dumps(productos_data)

        user_depto_pk = None
        if hasattr(self.request.user, 'perfil') and self.request.user.perfil.departamento:
            user_depto_pk = self.request.user.perfil.departamento.pk
            
        context['user_depto_pk'] = user_depto_pk
        context['is_admin'] = self.request.user.perfil.es_admin
        
        return context
    
    def form_valid(self, form):
        # ... (Sin cambios) ...
        form.instance.usuario_registra = self.request.user
        tipo = form.cleaned_data.get('tipo')
        
        if tipo == 'ENTRADA':
            producto = form.cleaned_data.get('producto')
            costo_bs = form.cleaned_data.get('costo_unitario_bs') 
            tasa = form.cleaned_data.get('tasa_cambio')
            
            if (producto and producto.unidad_medida and producto.unidad_medida > 0 
                and costo_bs and costo_bs > 0 and tasa and tasa > 0):
                costo_paquete_usd = costo_bs / tasa
                costo_unidad_usd = costo_paquete_usd / producto.unidad_medida
                form.instance.costo_unitario_usd = costo_unidad_usd
            else:
                form.instance.costo_unitario_usd = None
        else:
            form.instance.costo_unitario_usd = None
        try:
            return super().form_valid(form)
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        
@method_decorator(never_cache, name='dispatch')
class MovimientoUpdateView(LoginRequiredMixin, UpdateView):
    # ... (Sin cambios) ...
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
    # ... (Sin cambios) ...
    depto = get_object_or_404(
        Departamento.objects.prefetch_related(
            'perfiles__user', 
            'stock_items__producto'
        ), 
        pk=pk
    )

    perfil = request.user.perfil
    if not perfil.es_admin and perfil.departamento != depto:
        return HttpResponse("Permiso Denegado. Solo puede ver reportes de su propio departamento.", status=403)

    stock_items = [
        item for item in depto.stock_items.all() if item.cantidad > 0
    ]
    context = {
        'depto': depto,
        'stock_items': stock_items,
        'fecha_actual': timezone.now(), 
    }
    
    html_string = render_to_string('stock/reporte_pdf_template.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="reporte_stock_{depto.nombre}.pdf"'
    return response

# =========================================================================
# VISTAS AJAX (¡MODIFICADAS Y NUEVAS!)
# =========================================================================

def load_categorias(request):
    """
    Carga categorías para el select dinámico.
    - Si se pasa 'departamento_id', filtra categorías que tengan al menos
      un producto con stock > 0 en ese departamento.
    """
    departamento_id = request.GET.get('departamento_id')
    
    if departamento_id:
        # --- ¡NUEVA LÓGICA MÁS ROBUSTA! ---
        # 1. Obtener todos los IDs de productos que tienen stock en ese depto
        product_ids_in_stock = StockActual.objects.filter(
            departamento_id=departamento_id,
            cantidad__gt=0
        ).values_list('producto_id', flat=True)

        # 2. De esos IDs, obtener los IDs de sus categorías
        # (Asumiendo que 'categoria_id' puede ser NULL)
        category_ids = Producto.objects.filter(
            pk__in=product_ids_in_stock
        ).exclude(
            categoria_id=None
        ).values_list('categoria_id', flat=True).distinct()

        # 3. Obtener los objetos Categoria
        categorias = Categoria.objects.filter(pk__in=category_ids).order_by('nombre')
        # --- FIN NUEVA LÓGICA ---
    else:
        # Cargar todas las categorías (para ENTRADA)
        categorias = Categoria.objects.all().order_by('nombre')
    
    categorias_list = [{'id': str(c.pk), 'nombre': c.nombre} for c in categorias]
    return JsonResponse(categorias_list, safe=False)


def get_stock_departamento(request):
    """
    Obtiene el stock completo de un departamento (HTML) para mostrarlo en el panel
    de información de 'Transferencia'.
    """
    # ... (Sin cambios) ...
    departamento_id = request.GET.get('departamento_id')
    if not departamento_id:
        return JsonResponse({'error': 'No se proporcionó departamento'}, status=400)
    
    depto = get_object_or_404(Departamento, pk=departamento_id)
    
    stock_items = StockActual.objects.filter(
        departamento=depto,
        cantidad__gt=0
    ).select_related('producto', 'producto__categoria').order_by(
        'producto__categoria__nombre', 'producto__nombre'
    )
    
    stock_agrupado = {}
    for item in stock_items:
        categoria_nombre = "Sin Categoría"
        if item.producto.categoria:
             categoria_nombre = item.producto.categoria.nombre
        
        if categoria_nombre not in stock_agrupado:
            stock_agrupado[categoria_nombre] = []
            
        stock_agrupado[categoria_nombre].append({
            'nombre': item.producto.nombre,
            'cantidad': item.cantidad,
            'unidad_medida': item.producto.unidad_medida,
            'total_unidades': item.total_unidades 
        })
        
    html_content = render_to_string('movimiento/snippet_stock_departamento.html', {
        'depto': depto,
        'stock_agrupado': stock_agrupado,
        'total_items': stock_items.count()
    })
    
    return JsonResponse({'html_content': html_content})


def load_productos(request):
    """
    Carga productos para el select dinámico. (MODIFICADA)
    """
    # ... (Sin cambios) ...
    categoria_id = request.GET.get('categoria_id')
    departamento_id = request.GET.get('departamento_id') 
    
    if not categoria_id:
        return JsonResponse([], safe=False)
        
    base_productos = Producto.objects.filter(categoria_id=categoria_id, activo=True).order_by('nombre')
    productos_list = []

    if departamento_id:
        stock_data = StockActual.objects.filter(
            departamento_id=departamento_id,
            producto__categoria_id=categoria_id,
            cantidad__gt=0
        ).values('producto_id', 'cantidad')
        
        stock_dict = {str(item['producto_id']): item['cantidad'] for item in stock_data}
        producto_ids_con_stock = stock_dict.keys()
        productos = base_productos.filter(pk__in=producto_ids_con_stock)
        
        for producto in productos:
            productos_list.append({
                'id': str(producto.pk),
                'nombre': f"{producto.nombre} ({producto.unidad_medida} u/paq)",
                'stock': str(stock_dict.get(str(producto.pk), 0))
            })
    
    else:
        for producto in base_productos:
            productos_list.append({
                'id': str(producto.pk), 
                'nombre': f"{producto.nombre} ({producto.unidad_medida} u/paq)",
                'stock': None
            })
            
    return JsonResponse(productos_list, safe=False)