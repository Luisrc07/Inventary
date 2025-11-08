# -------------------------------------------------------------------------
# Copyright (C) 2025 Luisrc07 - Luis Rodriguez
#
# Este programa es software libre: usted puede redistribuirlo y/o modificarlo
# bajo los términos de la Licencia Pública General GNU publicada
# por la Free Software Foundation, ya sea la versión 3 de la Licencia,
# o (a su elección) cualquier versión posterior.
#
# Este programa se distribuye con la esperanza de que sea útil, pero
# SIN NINGUNA GARANTÍA; sin incluso la garantía implícita de
# COMERCIABILIDAD o IDONEIDAD PARA UN PROPÓSITO PARTICULAR.
# Consulte la Licencia Pública General GNU para más detalles.
#
# Usted debería haber recibido una copia de la Licencia Pública General GNU
# junto con este programa. Si no, consulte <https://www.gnu.org/licenses/>.
# -------------------------------------------------------------------------

from django.shortcuts import render, HttpResponse, redirect
from django.urls import reverse_lazy 
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Sum, Q, F
import json

# Importar los modelos de tus otras apps
from movimientoAPP.models import Movimiento, StockActual
from inventarioAPP.models import Producto
from departamentoAPP.models import Departamento

# Create your views here.

def base(request):
    return render(request, "base.html")

# ==========================================================
# VISTA DEL DASHBOARD (CORREGIDA)
# ==========================================================
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html' 
    login_url = reverse_lazy('usuario:login') 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        perfil = user.perfil 
        today = timezone.now().date()

        # -----------------------------------------------------------------
        # LÓGICA PARA EL ADMINISTRADOR (VE TODO)
        # -----------------------------------------------------------------
        if perfil.es_admin:
            context['is_admin'] = True

            # 1. KPIs (Sin cambios)
            kpi_total_paquetes = StockActual.objects.aggregate(total=Sum('cantidad'))['total']
            kpi_movs_hoy = Movimiento.objects.filter(fecha__date=today).count()
            kpi_deptos_activos = Departamento.objects.filter(activo=True).count()
            
            alertas_qs = StockActual.objects.filter(
                cantidad__lt=F('producto__stock_minimo')
            ).select_related('producto', 'departamento').order_by('departamento__nombre', 'producto__nombre')
            
            kpi_alertas_stock = alertas_qs.count()

            # 2. Listas (Sin cambios)
            context['alertas_stock'] = alertas_qs[:10] 
            context['actividad_reciente'] = Movimiento.objects.all().select_related(
                'producto', 'departamento_origen', 'departamento_destino'
            ).order_by('-fecha')[:5]

            # 3. Datos para Gráficos (Admin)
            
            # Gráfico 1: Stock por Departamento (Este estaba bien)
            depto_data = Departamento.objects.filter(activo=True).annotate(
                total_paquetes=Sum('stock_items__cantidad')
            ).filter(total_paquetes__gt=0).order_by('-total_paquetes')
            
            context['chart_depto_labels'] = json.dumps([d.nombre for d in depto_data])
            context['chart_depto_data'] = json.dumps([float(d.total_paquetes or 0) for d in depto_data])

            # ================================================================
            # ¡CORRECCIÓN AQUÍ!
            # Gráfico 2: Top 5 Productos (Global)
            # ANTES: stock_total=Sum('stockactual_set__cantidad')
            # AHORA: stock_total=Sum('stockactual__cantidad') 
            #        (basado en el FieldError que nos diste)
            # ================================================================
            top_productos = Producto.objects.annotate(
                stock_total=Sum('stockactual__cantidad') # <-- ¡CORREGIDO!
            ).filter(stock_total__gt=0).order_by('-stock_total')[:5]
            
            context['chart_top_productos_labels'] = json.dumps([p.nombre for p in top_productos])
            context['chart_top_productos_data'] = json.dumps([float(p.stock_total or 0) for p in top_productos])

        # -----------------------------------------------------------------
        # LÓGICA PARA GERENTE / OPERADOR (Sin cambios)
        # -----------------------------------------------------------------
        else:
            context['is_admin'] = False
            mi_departamento = perfil.departamento
            
            if mi_departamento:
                # ... (resto de la lógica de gerente sin cambios) ...
                kpi_total_paquetes = StockActual.objects.filter(
                    departamento=mi_departamento
                ).aggregate(total=Sum('cantidad'))['total']
                
                kpi_movs_hoy = Movimiento.objects.filter(
                    Q(departamento_origen=mi_departamento) | Q(departamento_destino=mi_departamento),
                    fecha__date=today
                ).count()
                
                kpi_deptos_activos = 1 
                
                alertas_qs = StockActual.objects.filter(
                    departamento=mi_departamento,
                    cantidad__lt=F('producto__stock_minimo')
                ).select_related('producto').order_by('producto__nombre')
                
                kpi_alertas_stock = alertas_qs.count()
                context['alertas_stock'] = alertas_qs[:10]
                context['actividad_reciente'] = Movimiento.objects.filter(
                    Q(departamento_origen=mi_departamento) | Q(departamento_destino=mi_departamento)
                ).select_related('producto', 'departamento_origen', 'departamento_destino').order_by('-fecha')[:5]
                
            else:
                kpi_total_paquetes = 0
                kpi_movs_hoy = 0
                kpi_deptos_activos = 0
                kpi_alertas_stock = 0
                context['alertas_stock'] = []
                context['actividad_reciente'] = []

        # Pasar KPIs comunes al contexto
        context['kpi_total_paquetes'] = kpi_total_paquetes
        context['kpi_movs_hoy'] = kpi_movs_hoy
        context['kpi_deptos_activos'] = kpi_deptos_activos
        context['kpi_alertas_stock'] = kpi_alertas_stock
        
        return context


# ==========================================================
# VISTA DE REDIRECCIÓN (Sin cambios)
# ==========================================================

def root_redirect_view(request):
    """
    Redirige al 'dashboard' si el usuario está logueado,
    o al 'login' si no lo está.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard') 
    
    return redirect('usuario:login')