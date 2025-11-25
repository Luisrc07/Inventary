# -------------------------------------------------------------------------
# views.py (COPIA Y REEMPLAZA TODO EL CONTENIDO)
# -------------------------------------------------------------------------

import json
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView
from django.views import View # <--- Necesario para la nueva lógica
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse 
from django.db.models import Q, F, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string, get_template
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from xhtml2pdf import pisa
from django.db import transaction 

# Importaciones de Modelos
from .models import Movimiento, StockActual
from inventarioAPP.models import Producto, Categoria 
from departamentoAPP.models import Departamento
from proveedorAPP.models import Proveedor 

# Importaciones de Formularios (Asegúrate que forms.py tenga estas clases)
from .forms import MovimientoForm, MovimientoCabeceraForm, MovimientoFormSet

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# =========================================================================
# VISTAS DE STOCK (Se mantienen igual)
# =========================================================================

@method_decorator(never_cache, name='dispatch')
class StockGroupedListview(LoginRequiredMixin, ListView):
    model = Departamento 
    template_name = 'stock/list_grouped.html' 
    context_object_name = 'departamentos'
    
    def get_queryset(self):
        perfil = self.request.user.perfil
        base_qs = Departamento.objects.filter(activo=True).prefetch_related(
            'perfiles__user', 'stock_items__producto'
        )
        if perfil.es_admin:
            return base_qs
        return base_qs.filter(pk=perfil.departamento.pk)

@method_decorator(never_cache, name='dispatch')
class StockListview(LoginRequiredMixin, ListView):
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
# VISTAS DE MOVIMIENTO
# =========================================================================

@method_decorator(never_cache, name='dispatch')
class MovimientoListview(LoginRequiredMixin, ListView):
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

# --- ESTA ES LA CLASE MODIFICADA PARA CARGA MÚLTIPLE ---
@method_decorator(never_cache, name='dispatch')
class MovimientoCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Vista personalizada que maneja Cabecera + Lista de Productos (FormSet).
    Permite guardar múltiples productos en una sola transacción.
    """
    template_name = 'movimiento/form.html'

    def test_func(self):
        return self.request.user.perfil.es_admin or self.request.user.perfil.es_gerente

    def get(self, request, *args, **kwargs):
        # 1. Instanciamos formulario de cabecera y el conjunto de formularios (formset) vacíos
        cabecera_form = MovimientoCabeceraForm(user=request.user)
        formset = MovimientoFormSet()
        
        # 2. Preparamos datos JSON para cálculos en Javascript (Unidad de Medida)
        productos_data = {str(p.id): str(p.unidad_medida) for p in Producto.objects.filter(activo=True)}
        
        user_depto_pk = None
        if hasattr(request.user, 'perfil') and request.user.perfil.departamento:
            user_depto_pk = request.user.perfil.departamento.pk

        return render(request, self.template_name, {
            'cabecera_form': cabecera_form,
            'formset': formset,
            'productos_data_json': json.dumps(productos_data),
            'is_admin': request.user.perfil.es_admin,
            'user_depto_pk': user_depto_pk,
            'is_edit_mode': False
        })

    def post(self, request, *args, **kwargs):
        cabecera_form = MovimientoCabeceraForm(request.POST, user=request.user)
        formset = MovimientoFormSet(request.POST)
        
        # Recargamos data de productos por si hay error
        productos_data = {str(p.id): str(p.unidad_medida) for p in Producto.objects.filter(activo=True)}

        if cabecera_form.is_valid() and formset.is_valid():
            data_comun = cabecera_form.cleaned_data
            tipo = data_comun['tipo']
            count_registrados = 0

            try:
                with transaction.atomic(): # Asegura integridad: se guardan todos o ninguno
                    for form in formset:
                        # Verificamos que la fila no esté vacía (tenga producto y cantidad)
                        if form.cleaned_data and form.cleaned_data.get('producto') and form.cleaned_data.get('cantidad'):
                            producto = form.cleaned_data['producto']
                            cantidad = form.cleaned_data['cantidad']
                            costo_bs = form.cleaned_data.get('costo_unitario_bs')
                            
                            # Creamos el objeto Movimiento
                            mov = Movimiento(
                                tipo=tipo,
                                usuario_registra=request.user,
                                departamento_origen=data_comun.get('departamento_origen'),
                                departamento_destino=data_comun.get('departamento_destino'),
                                proveedor=data_comun.get('proveedor'),
                                numero_factura=data_comun.get('numero_factura'),
                                tasa_cambio=data_comun.get('tasa_cambio'),
                                observaciones=data_comun.get('observaciones'),
                                producto=producto,
                                cantidad=cantidad,
                                costo_unitario_bs=costo_bs
                            )

                            # Cálculo especial de Costo USD (Solo para Entradas)
                            # Para Salidas/Transferencias, el modelo se encarga de heredar el costo
                            if tipo == 'ENTRADA':
                                tasa = data_comun.get('tasa_cambio')
                                if producto.unidad_medida and costo_bs and tasa and tasa > 0:
                                    costo_paq_usd = float(costo_bs) / float(tasa)
                                    mov.costo_unitario_usd = costo_paq_usd / float(producto.unidad_medida)
                            
                            mov.save() # Al guardar, el modelo descuenta/suma al stock
                            count_registrados += 1
                
                if count_registrados > 0:
                    messages.success(request, f"Éxito: Se registraron {count_registrados} movimientos correctamente.")
                    return redirect('movimientoAPP:movimiento_list')
                else:
                    messages.warning(request, "La lista de productos estaba vacía. No se guardó nada.")

            except Exception as e:
                messages.error(request, f"Error al guardar: {str(e)}")
        
        else:
            messages.error(request, "Hay errores en el formulario. Por favor revise los campos resaltados en rojo.")

        # Si hubo error, volvemos a renderizar con los datos ingresados
        return render(request, self.template_name, {
            'cabecera_form': cabecera_form,
            'formset': formset,
            'productos_data_json': json.dumps(productos_data),
            'is_admin': request.user.perfil.es_admin,
            'user_depto_pk': request.user.perfil.departamento.pk if request.user.perfil.departamento else None,
            'is_edit_mode': False
        })

@method_decorator(never_cache, name='dispatch')
class MovimientoUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista simple para editar solo observaciones de un movimiento existente.
    """
    model = Movimiento
    form_class = MovimientoForm # Usa el form simple (solo observaciones)
    template_name = 'movimiento/form.html'
    success_url = reverse_lazy('movimientoAPP:movimiento_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit_mode'] = True # Bandera clave para el template
        return context

# =========================================================================
# VISTA DE REPORTE PDF
# =========================================================================

def generar_reporte_stock_pdf(request, pk):
    depto = get_object_or_404(
        Departamento.objects.prefetch_related('perfiles__user', 'stock_items__producto'), pk=pk
    )
    perfil = request.user.perfil
    if not perfil.es_admin and perfil.departamento != depto:
        return HttpResponse("Permiso Denegado.", status=403)

    stock_items = [item for item in depto.stock_items.all() if item.cantidad > 0]
    
    context = {'depto': depto, 'stock_items': stock_items, 'fecha_actual': timezone.now()}
    template_path = 'stock/reporte_pdf_template.html'
    template = get_template(template_path)
    html = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="reporte_stock_{depto.nombre}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
       return HttpResponse('Hubo errores al generar el PDF <pre>' + html + '</pre>')
    return response

# =========================================================================
# VISTAS AJAX 
# =========================================================================

def load_categorias(request):
    departamento_id = request.GET.get('departamento_id')
    
    if departamento_id:
        product_ids_in_stock = StockActual.objects.filter(
            departamento_id=departamento_id, cantidad__gt=0
        ).values_list('producto_id', flat=True)

        category_ids = Producto.objects.filter(
            pk__in=product_ids_in_stock
        ).exclude(categoria__isnull=True).values_list('categoria_id', flat=True).distinct()

        categorias = Categoria.objects.filter(pk__in=category_ids).order_by('nombre')
    else:
        categorias = Categoria.objects.all().order_by('nombre')
    
    return JsonResponse([{'id': str(c.pk), 'nombre': c.nombre} for c in categorias], safe=False)

def get_stock_departamento(request):
    departamento_id = request.GET.get('departamento_id')
    if not departamento_id:
        return JsonResponse({'error': 'No se proporcionó departamento'}, status=400)
    
    depto = get_object_or_404(Departamento, pk=departamento_id)
    
    stock_items = StockActual.objects.filter(
        departamento=depto, cantidad__gt=0
    ).select_related('producto', 'producto__categoria').annotate(
        categoria_orden=Coalesce('producto__categoria__nombre', Value('Sin Categoría'))
    ).order_by('categoria_orden', 'producto__nombre')
    
    stock_agrupado = {}
    for item in stock_items:
        cat_name = item.producto.categoria.nombre if item.producto.categoria else "Sin Categoría"
        if cat_name not in stock_agrupado: stock_agrupado[cat_name] = []
        stock_agrupado[cat_name].append({
            'nombre': item.producto.nombre,
            'cantidad': item.cantidad,
            'unidad_medida': item.producto.unidad_medida, 
            'total_unidades': item.total_unidades
        })
    
    html_content = render_to_string('movimiento/snippet_stock_departamento.html', {
        'depto': depto, 'stock_agrupado': stock_agrupado
    })
    return JsonResponse({'html_content': html_content})

def load_productos(request):
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
        # Solo productos que tengan stock
        productos = base_productos.filter(pk__in=stock_dict.keys())
        
        for producto in productos:
            productos_list.append({
                'id': str(producto.pk),
                'nombre': f"{producto.nombre} ({producto.unidad_medida} u/paq)",
                'stock': str(stock_dict.get(str(producto.pk), 0)),
                'unidad_medida': str(producto.unidad_medida) 
            })
    else:
        for producto in base_productos:
            productos_list.append({
                'id': str(producto.pk), 
                'nombre': f"{producto.nombre} ({producto.unidad_medida} u/paq)",
                'stock': None,
                'unidad_medida': str(producto.unidad_medida)
            })
            
    return JsonResponse(productos_list, safe=False)