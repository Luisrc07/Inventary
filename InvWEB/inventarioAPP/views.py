from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from inventarioAPP.models import Categoria, Producto
from django.db.models import ProtectedError
from django.contrib import messages
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
    success_url = reverse_lazy('inventarioAPP:categoria_list')

class CategoriaUpdateView(UpdateView):
    model = Categoria
    template_name = 'categoria/form.html' # CORREGIDO
    form_class = CategoriaForm
    success_url = reverse_lazy('inventarioAPP:categoria_list')

class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'categoria/confirm_delete.html' # CORREGIDO
    success_url = reverse_lazy('inventarioAPP:categoria_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # El objeto a eliminar es 'self.object'
        # Añadimos una variable booleana para la condicional en la plantilla
        context['has_products'] = self.object.productos.exists() 
        # Si usaste related_name='productos' en el modelo Producto, usa:
        # context['has_products'] = self.object.productos.exists()
        
        # También puedes pasar el conteo exacto si lo necesitas (aunque .exists() es más eficiente)
        context['product_count'] = self.object.productos.count() 
        
        return context

    # El manejo de ProtectedError ya está correcto para cuando el formulario se envía (POST)
    def post(self, request, *args, **kwargs):
        try:
            # Llama al método post original que intenta eliminar el objeto
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            # 1. Añadir el mensaje de error de Django
            messages.error(
                request, 
                'No se puede eliminar la categoría porque tiene productos asociados. '
                'Elimine o reasigne los productos primero.'
            )
            # 2. Redirigir de vuelta a la lista de categorías
            return redirect('inventarioAPP:categoria_list')
#producto
class ProductoListview(ListView):
    model = Producto
    template_name = 'producto/list.html' # CORREGIDO
    context_object_name = 'productos'

class ProductoCreateView(CreateView):
    model = Producto
    template_name = 'producto/form.html' # CORREGIDO
    form_class = ProductoForm
    success_url = reverse_lazy('inventarioAPP:producto_list')

class ProductoUpdateView(UpdateView):
    model = Producto
    template_name = 'producto/form.html' # CORREGIDO
    form_class = ProductoForm
    success_url = reverse_lazy('inventarioAPP:producto_list')

class ProductoDeleteView(DeleteView):
    model = Producto
    template_name = 'producto/confirm_delete.html' # CORREGIDO
    success_url = reverse_lazy('inventarioAPP:producto_list')

