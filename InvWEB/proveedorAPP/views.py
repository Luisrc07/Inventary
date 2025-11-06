from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from proveedorAPP.models import Proveedor
# Create your views here.
from proveedorAPP.forms import ProveedorForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import ProtectedError
# Create your views here.
class ProveedorListview(LoginRequiredMixin, ListView):
    model = Proveedor
    template_name = 'proveedor/list.html' # CORREGIDO
    context_object_name = 'proveedores'

class ProveedorCreateView(LoginRequiredMixin, CreateView):
    model = Proveedor
    template_name = 'proveedor/form.html' # CORREGIDO
    form_class = ProveedorForm
    success_url = reverse_lazy('proveedorAPP:prov_list')

class ProveedorUpdateView(LoginRequiredMixin, UpdateView):
    model = Proveedor
    template_name = 'proveedor/form.html' # CORREGIDO
    form_class = ProveedorForm
    success_url = reverse_lazy('proveedorAPP:prov_list')

class ProveedorDeleteView(LoginRequiredMixin, DeleteView):
    model = Proveedor
    # Asegúrate de que esta ruta de plantilla sea correcta
    template_name = 'proveedor/confirm_delete.html'
    success_url = reverse_lazy('proveedorAPP:prov_list') # O como se llame tu lista

    def get_context_data(self, **kwargs):
        """
        Pasamos el conteo de dependencias (movimientos) a la plantilla.
        """
        context = super().get_context_data(**kwargs)
        proveedor = self.get_object()
        
        # Contamos cuántos Movimientos están usando este proveedor.
        # 'movimiento_set' es el nombre de la relación inversa.
        context['dependency_count'] = proveedor.movimiento_set.count()
        return context

    def post(self, request, *args, **kwargs):
        """
        Bloqueamos el POST si el proveedor tiene movimientos asociados.
        """
        self.object = self.get_object()
        
        # Obtenemos el conteo de nuevo por seguridad
        dependency_count = self.object.movimiento_set.count()

        if dependency_count > 0:
            # Si hay dependencias, bloqueamos la eliminación
            messages.error(request, (
                f"ERROR: No se puede eliminar al proveedor '{self.object.nombre}' "
                "porque tiene movimientos de entrada registrados."
            ))
            return redirect(self.success_url)

        # Si el conteo es 0, procedemos a borrar
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(request, f"Proveedor '{self.object.nombre}' eliminado con éxito.")
            return response

        except ProtectedError: 
            # Doble seguro (ya que tu modelo usa on_delete=PROTECT)
            messages.error(request, (
                f"ERROR: No se puede eliminar '{self.object.nombre}' "
                "debido a una restricción de la base de datos (ProtectedError)."
            ))
            return redirect(self.success_url)
