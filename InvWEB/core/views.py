from django.shortcuts import render, HttpResponse
# Create your views here.
from django.shortcuts import redirect


def base(request):
    return render(request, "base.html")

# En usuario/views.py



def root_redirect_view(request):
    """
    Redirige al 'inicio' si el usuario está logueado,
    o al 'login' si no lo está.
    """
    if request.user.is_authenticated:
        # Asumiendo que tienes una URL llamada 'inicio'
        return redirect('inicio') 
    
    # [cite_start]Redirige a la URL 'login' de tu app 'usuario' [cite: 5]
    return redirect('usuario:login')
