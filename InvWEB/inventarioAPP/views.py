from django.shortcuts import render

# Create your views here.

def producto_list(request):
    return render(request, "producto_list.html")