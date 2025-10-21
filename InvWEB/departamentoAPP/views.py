from django.shortcuts import render

# Create your views here.

def departamento_list(request):
    return render(request, "departamento_list.html")