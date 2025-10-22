from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from inventarioAPP.models import Categoria, Producto

# Create your views here.
from inventarioAPP.forms import ProductoForm, CategoriaForm


class CategoriaListview(ListView):
    model = Categoria
    template_name = 'categoria/list.html' # CORREGIDO
    context_object_name = 'categoria'

class CategoriaCreateView(CreateView):
    model = Categoria
    template_name = 'categoria/form.html' # CORREGIDO
    form_class = CategoriaForm
    success_url = reverse_lazy('categoriaAPP:encargado_list')

class CategoriaUpdateView(UpdateView):
    model = Categoria
    template_name = 'categoria/form.html' # CORREGIDO
    form_class = CategoriaForm
    success_url = reverse_lazy('categoriaAPP:encargado_list')

class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'categoria/confirm_delete.html' # CORREGIDO
    success_url = reverse_lazy('categoriaAPP:encargado_list')


#producto
class ProductoListview(ListView):
    model = Producto
    template_name = 'producto/list.html' # CORREGIDO
    context_object_name = 'productos'

class ProductoCreateView(CreateView):
    model = Producto
    template_name = 'producto/form.html' # CORREGIDO
    form_class = ProductoForm
    success_url = reverse_lazy('productoAPP:producto_list')

class ProductoUpdateView(UpdateView):
    model = Producto
    template_name = 'producto/form.html' # CORREGIDO
    form_class = ProductoForm
    success_url = reverse_lazy('productoAPP:producto_list')

class ProductoDeleteView(DeleteView):
    model = Producto
    template_name = 'producto/confirm_delete.html' # CORREGIDO
    success_url = reverse_lazy('productoAPP:producto_list')

