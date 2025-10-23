from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from movimientoAPP.models import Movimiento, StockActual
from django.db.models import ProtectedError
from django.contrib import messages
# Create your views here.
from movimientoAPP.forms import MovimientoForm, StockForm


#movimiento
class MovimientoListview(ListView):
    model = Movimiento
    template_name = 'movimiento/list.html' # CORREGIDO
    context_object_name = 'movimiento'

class MovimientoCreateView(CreateView):
    model = Movimiento
    template_name = 'movimiento/form.html' # CORREGIDO
    form_class = MovimientoForm
    success_url = reverse_lazy('movimientoAPP:movimiento_list')

class MovimientoUpdateView(UpdateView):
    model = Movimiento
    template_name = 'movimiento/form.html' # CORREGIDO
    form_class = MovimientoForm
    success_url = reverse_lazy('movimientoAPP:movimiento_list')

class MovimientoDeleteView(DeleteView):
    model = Movimiento
    template_name = 'movimiento/confirm_delete.html' # CORREGIDO
    success_url = reverse_lazy('movimientoAPP:movimiento_list')

    
#Stock
class StockListview(ListView):
    model = StockActual
    template_name = 'stock/list.html' # CORREGIDO
    context_object_name = 'stockactual'

class StockCreateView(CreateView):
    model = StockActual
    template_name = 'stock/form.html' # CORREGIDO
    form_class = StockForm
    success_url = reverse_lazy('movimientoAPP:stock_list')

class StockUpdateView(UpdateView):
    model = StockActual
    template_name = 'stock/form.html' # CORREGIDO
    form_class = StockForm
    success_url = reverse_lazy('movimientoAPP:stock_list')

class StockDeleteView(DeleteView):
    model = StockActual
    template_name = 'stock/confirm_delete.html' # CORREGIDO
    success_url = reverse_lazy('movimientoAPP:stock_list')

