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
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Departamento
from .forms import DepartamentoForm


class DepartamentoListView(LoginRequiredMixin, ListView):
    """
    Muestra la lista de departamentos, PERO SÓLO LOS ACTIVOS.
    """
    model = Departamento
    template_name = 'departamento/list.html'
    context_object_name = 'departamentos'

   
        # ¡CORRECCIÓN! Solo mostrar departamentos que estén activos.
      

    def get_context_data(self, **kwargs):
        # Pasa el perfil a la plantilla para ocultar el botón "Crear"
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'perfil'):
            context['perfil'] = self.request.user.perfil
        return context


class DepartamentoCreateView(LoginRequiredMixin, CreateView):
    """
    Vista de CREAR. La plantilla 'form.html' se encargará
    de mostrar el formulario o el mensaje de "Bloqueado".
    """
    model = Departamento
    template_name = 'departamento/form.html'
    form_class = DepartamentoForm
    success_url = reverse_lazy('departamentoAPP:departamento_list')

    def get_context_data(self, **kwargs):
        # Pasa la variable 'is_admin' a la plantilla
        context = super().get_context_data(**kwargs)
        context['is_admin'] = hasattr(self.request.user, 'perfil') and self.request.user.perfil.es_admin
        return context

    def post(self, request, *args, **kwargs):
        # Chequeo de seguridad en el backend
        if not (hasattr(self.request.user, 'perfil') and self.request.user.perfil.es_admin):
            messages.error(self.request, "Acción no permitida. No tienes permisos de administrador.")
            return redirect('departamentoAPP:departamento_list')
        
        messages.success(request, "Departamento creado con éxito.")
        return super().post(request, *args, **kwargs)


class DepartamentoUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista de EDITAR. La plantilla 'form.html' se encargará
    de mostrar el formulario o el mensaje de "Bloqueado".
    """
    model = Departamento
    template_name = 'departamento/form.html'
    form_class = DepartamentoForm
    success_url = reverse_lazy('departamentoAPP:departamento_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = hasattr(self.request.user, 'perfil') and self.request.user.perfil.es_admin
        return context

    def post(self, request, *args, **kwargs):
        # Chequeo de seguridad en el backend
        if not (hasattr(self.request.user, 'perfil') and self.request.user.perfil.es_admin):
            messages.error(self.request, "Acción no permitida. No tienes permisos de administrador.")
            return redirect('departamentoAPP:departamento_list')
        
        messages.success(request, f"Departamento '{self.get_object()}' actualizado con éxito.")
        return super().post(request, *args, **kwargs)


class DepartamentoDeleteView(LoginRequiredMixin, DeleteView):
    """
    Vista de DESACTIVAR (Soft Delete).
    Maneja el GET para mostrar la confirmación.
    Maneja el POST para realizar la desactivación.
    """
    model = Departamento
    template_name = 'departamento/confirm_delete.html'
    success_url = reverse_lazy('departamentoAPP:departamento_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = hasattr(self.request.user, 'perfil') and self.request.user.perfil.es_admin
        
        depto = self.get_object()
        perfiles_asociados = depto.perfiles.count() 
        stock_asociado = depto.stock_items.filter(cantidad__gt=0).count() 

        context['perfiles_asociados'] = perfiles_asociados
        context['stock_asociado'] = stock_asociado
        # Solo se puede desactivar si no hay usuarios NI stock
        context['puede_desactivar'] = (perfiles_asociados == 0 and stock_asociado == 0)
        
        return context

    def post(self, request, *args, **kwargs):
        """
        Sobreescribimos el método POST.
        En lugar de borrar, hacemos un SOFT DELETE (activo=False).
        """
        
        # 1. Chequeo de Admin
        if not (hasattr(self.request.user, 'perfil') and self.request.user.perfil.es_admin):
            messages.error(self.request, "Acción no permitida. No tienes permisos de administrador.")
            return redirect('departamentoAPP:departamento_list')

        depto = self.get_object()
        
        # 2. Chequeo de dependencias (igual que en get_context_data)
        perfiles_count = depto.perfiles.count()
        stock_count = depto.stock_items.filter(cantidad__gt=0).count()
        
        if perfiles_count > 0 or stock_count > 0:
            messages.error(request, f"No se puede desactivar '{depto.nombre}'. Primero reasigna sus {perfiles_count} usuarios y vacía su stock.")
            return redirect(self.success_url)

        # 3. ¡LA ACCIÓN DE SOFT DELETE!
        depto.activo = False
        depto.save()
        
        messages.success(request, f"Departamento '{depto.nombre}' ha sido DESACTIVADO (eliminación lógica).")
        return redirect(self.success_url)