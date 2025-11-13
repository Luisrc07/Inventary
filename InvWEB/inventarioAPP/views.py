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

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from inventarioAPP.models import Categoria, Producto
from django.db.models import ProtectedError
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.
from inventarioAPP.forms import ProductoForm, CategoriaForm
from django.db.models import Count

class CategoriaListview(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = 'categoria/list.html' 
    context_object_name = 'categoria'

class CategoriaCreateView(LoginRequiredMixin, CreateView):
    model = Categoria
    template_name = 'categoria/form.html' 
    form_class = CategoriaForm
    success_url = reverse_lazy('inventarioAPP:categoria_list')

class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Categoria
    template_name = 'categoria/form.html' 
    form_class = CategoriaForm
    success_url = reverse_lazy('inventarioAPP:categoria_list')

class CategoriaDeleteView(LoginRequiredMixin, DeleteView):
    model = Categoria
    template_name = 'categoria/confirm_delete.html' 
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
class ProductoListview(LoginRequiredMixin, ListView):
    model = Producto
    template_name = 'producto/list.html' 
    context_object_name = 'productos'

    def get_queryset(self):
        # Usamos annotate() para añadir un campo 'movimiento_count' a cada producto
        return Producto.objects.annotate(
            movimiento_count=Count('movimiento') # 'movimiento' es el related_name
        ).order_by('nombre')

class ProductoCreateView(LoginRequiredMixin, CreateView):
    model = Producto
    template_name = 'producto/form.html' 
    form_class = ProductoForm
    success_url = reverse_lazy('inventarioAPP:producto_list')

class ProductoUpdateView(LoginRequiredMixin, UpdateView):
    model = Producto
    template_name = 'producto/form.html' # CORREGIDO
    form_class = ProductoForm
    success_url = reverse_lazy('inventarioAPP:producto_list')

class ProductoDeleteView(LoginRequiredMixin, DeleteView):
    model = Producto
    # Asegúrate de crear este archivo de plantilla en el Paso 2
    template_name = 'producto/confirm_delete.html'
    success_url = reverse_lazy('inventarioAPP:producto_list')

    def get_context_data(self, **kwargs):
        """
        ¡AQUÍ ESTÁ LA LÓGICA!
        Pasamos el conteo de dependencias a la plantilla.
        """
        context = super().get_context_data(**kwargs)
        producto = self.get_object()
        
        # Contamos cuántos Movimientos y Stock están usando este producto.
        # 'movimiento_set' y 'stockactual_set' son los nombres por defecto
        # que Django usa para las relaciones inversas.
        mov_count = producto.movimiento_set.count()
        stock_count = producto.stockactual_set.count()
        
        context['dependency_count'] = mov_count + stock_count
        return context

    def post(self, request, *args, **kwargs):
        """
        Mantenemos el "cortafuegos" (firewall) por si acaso.
        Esto captura el ProtectedError si algo intenta forzar el borrado.
        """
        self.object = self.get_object()
        
        # Obtenemos el conteo OTRA VEZ por seguridad en el POST
        mov_count = self.object.movimiento_set.count()
        stock_count = self.object.stockactual_set.count()
        dependency_count = mov_count + stock_count

        if dependency_count > 0:
            # Si alguien fuerza el POST, lo bloqueamos
            messages.error(request, (
                f"ERROR: No se puede eliminar '{self.object.nombre}' "
                "porque tiene dependencias de stock o movimientos."
            ))
            return redirect(self.success_url)

        # Si el conteo es 0, procedemos a borrar
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(request, f"Producto '{self.object.nombre}' eliminado con éxito.")
            return response

        except ProtectedError: 
            # Doble seguro, aunque nuestro chequeo manual ya debería haberlo evitado
            messages.error(request, (
                f"ERROR: No se puede eliminar '{self.object.nombre}' "
                "debido a una restricción de la base de datos (ProtectedError)."
            ))
            return redirect(self.success_url)

