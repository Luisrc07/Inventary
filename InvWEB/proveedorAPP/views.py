from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from proveedorAPP.models import Proveedor
# Create your views here.
from proveedorAPP.forms import ProveedorForm


# Create your views here.
class ProveedorListview(ListView):
    model = Proveedor
    template_name = 'proveedor/list.html' # CORREGIDO
    context_object_name = 'proveedores'

class ProveedorCreateView(CreateView):
    model = Proveedor
    template_name = 'proveedor/form.html' # CORREGIDO
    form_class = ProveedorForm
    success_url = reverse_lazy('proveedorAPP:prov_list')

class ProveedorUpdateView(UpdateView):
    model = Proveedor
    template_name = 'proveedor/form.html' # CORREGIDO
    form_class = ProveedorForm
    success_url = reverse_lazy('proveedorAPP:prov_list')

class ProveedorDeleteView(DeleteView):
    model = Proveedor
    template_name = 'proveedor/confirm_delete.html' # CORREGIDO
    success_url = reverse_lazy('proveedorAPP:prov_list')


