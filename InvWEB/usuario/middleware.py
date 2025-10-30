from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:
    """
    Middleware que redirige al login a todos los usuarios
    que no estén autenticados.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        # Si el usuario ya está logueado, deja que continúe
        if request.user.is_authenticated:
            return self.get_response(request)

        # Si NO está logueado:
        
        # Obtenemos las URLs a las que SÍ puede entrar
        # (El login y el admin de Django)
        login_url = reverse('usuario:login')
        
        # Si la URL que pide es la de login o el admin,
        # lo dejamos pasar para que pueda loguearse.
        if request.path_info == login_url or request.path_info.startswith('/admin/'):
            return self.get_response(request)
            
        # Para CUALQUIER OTRA URL, lo redirigimos al login
        return redirect(login_url)