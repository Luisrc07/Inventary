# departamentoAPP/views.py

from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from departamentoAPP.models import Departamento, Encargado
# Create your views here.

 #Encargado
class EncargadoListview(ListView):
    model = Encargado
    template_name = 'encargado/list.html' # CORREGIDO
    context_object_name = 'encargados'

class EncargadoCreateView(CreateView):
    model = Encargado
    template_name = 'encargado/form.html' # CORREGIDO
    fields = ['nombres', 'apellidos', 'telefono', 'email', 'activo']
    success_url = reverse_lazy('departamentoAPP:encargado_list')

class EncargadoUpdateView(UpdateView):
    model = Encargado
    template_name = 'encargado/form.html' # CORREGIDO
    fields = ['nombres', 'apellidos', 'telefono', 'email', 'activo']
    success_url = reverse_lazy('departamentoAPP:encargado_list')

class EncargadoDeleteView(DeleteView):
    model = Encargado
    template_name = 'encargado/confirm_delete.html' # CORREGIDO
    success_url = reverse_lazy('departamentoAPP:encargado_list')



 # Departamento
class DepartamentoListView(ListView):
    model = Departamento
    template_name = 'departamento/list.html' # CORREGIDO
    context_object_name = 'departamentos'

class DepartamentoCreateView(CreateView):
    model = Departamento
    template_name = 'departamento/form.html' # CORREGIDO
    fields = ['nombre', 'descripcion', 'encargado', 'activo']
    success_url = reverse_lazy('departamentoAPP:departamento_list')

class DepartamentoUpdateView(UpdateView):
    model = Departamento
    template_name = 'departamento/form.html' # CORREGIDO
    fields = ['nombre', 'descripcion', 'encargado', 'activo']
    success_url = reverse_lazy('departamentoAPP:departamento_list')

class DepartamentoDeleteView(DeleteView):
    model = Departamento
    template_name = 'departamento/confirm_delete.html' # CORREGIDO
    success_url = reverse_lazy('departamentoAPP:departamento_list') # CORREGIDO