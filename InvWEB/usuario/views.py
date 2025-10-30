from django.shortcuts import redirect
from django.views.generic import FormView
from django.urls import reverse_lazy
from usuario.forms import RegistroForm
# ¡Importamos los dos Mixins que necesitamos!
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User # ¡Importa el modelo User!
from .forms import RegistroForm, UserUpdateForm # ¡Importa el nuevo form!
from .models import PerfilUsuario # ¡Importa PerfilUsuario!
from django.views.generic import ListView, UpdateView # ¡Importa ListView y UpdateView!

# Esta vista es para que un ADMIN registre a otros.
class RegistroUsuarioView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'usuario/registro.html'
    form_class = RegistroForm
    success_url = reverse_lazy('movimientoAPP:inicio') # A donde quieras

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
        
    # --- YA NO NECESITAS EL MÉTODO 'get' ---
    # El 'UserPassesTestMixin' se encarga de toda la seguridad
    # por lo que puedes BORRAR tu método get() anterior.

# --- NUEVA VISTA: LISTA DE USUARIOS ---
class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'usuario/user_list.html' # Una nueva plantilla
    context_object_name = 'usuarios'

    def test_func(self):
        # Solo Admins pueden ver esta lista
        return self.request.user.perfil.es_admin

    def get_queryset(self):
        # Optimizamos la consulta para incluir el perfil
        return User.objects.all().select_related('perfil__departamento')


# --- NUEVA VISTA: EDITAR USUARIO ---
class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = PerfilUsuario # ¡Editamos el Perfil!
    form_class = UserUpdateForm
    template_name = 'usuario/user_form.html' # Una nueva plantilla
    success_url = reverse_lazy('usuario:user_list') # Vuelve a la lista

    def test_func(self):
        # Solo Admins pueden editar
        return self.request.user.perfil.es_admin

    def get_object(self, queryset=None):
        """
        Obtenemos el PerfilUsuario basándonos en la PK del *User* que viene de la URL.
        """
        user_pk = self.kwargs.get('pk')
        return PerfilUsuario.objects.get(user__pk=user_pk)