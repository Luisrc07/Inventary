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

from django.shortcuts import redirect
from django.views.generic import FormView
from django.urls import reverse_lazy
from usuario.forms import RegistroForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User 
from .forms import RegistroForm, UserUpdateForm 
from .models import PerfilUsuario 
from django.views.generic import ListView, UpdateView 
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

# Esta vista es para que un ADMIN registre a otros.
@method_decorator(never_cache, name='dispatch')
class RegistroUsuarioView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'usuario/registro.html'
    form_class = RegistroForm
    success_url = reverse_lazy('movimientoAPP:inicio')

    def test_func(self):
        """
        Esta es la prueba de permiso.
        Se ejecuta ANTES de 'get' o 'post'.
        Si devuelve False, el usuario es redirigido.
        """
        # Revisa si el usuario tiene un perfil (es seguro)
        if not hasattr(self.request.user, 'perfil'):
            return False
        
        # Devuelve True si es admin, False si no lo es
        return self.request.user.perfil.es_admin

    def handle_no_permission(self):
        """
        (Opcional) Si test_func() devuelve False,
        lo redirigimos a 'inicio'.
        """
        return redirect('movimientoAPP:inicio')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    
def root_redirect_view(request):
    """
    Redirige al 'inicio' si el usuario está logueado,
    o al 'login' si no lo está.
    """
    if request.user.is_authenticated:
        # Asumiendo que tienes una URL llamada 'inicio'
        return redirect('movimientoAPP:inicio') 
    
    # [cite_start]Redirige a la URL 'login' de tu app 'usuario' [cite: 5]
    return redirect('usuario:login')
        


@method_decorator(never_cache, name='dispatch')
class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'usuario/user_list.html' 
    context_object_name = 'usuarios'

    def test_func(self):
        # Solo Admins pueden ver esta lista
        return self.request.user.perfil.es_admin

    def get_queryset(self):
        # Optimizamos la consulta para incluir el perfil
        return User.objects.all().select_related('perfil__departamento')



@method_decorator(never_cache, name='dispatch')
class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = PerfilUsuario 
    form_class = UserUpdateForm
    template_name = 'usuario/user_form.html' 
    success_url = reverse_lazy('usuario:user_list') 

    def test_func(self):
        # Solo Admins pueden editar
        return self.request.user.perfil.es_admin

    def get_object(self, queryset=None):
        """
        Obtenemos el PerfilUsuario basándonos en la PK del *User* que viene de la URL.
        """
        user_pk = self.kwargs.get('pk')
        return PerfilUsuario.objects.get(user__pk=user_pk)