from django.shortcuts import render, HttpResponse
# Create your views here.

def prueba(request):
    return render(request, "InvWEBAPP/prueba.html")