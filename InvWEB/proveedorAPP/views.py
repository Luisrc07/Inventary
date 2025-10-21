from django.shortcuts import render

# Create your views here.

def prov_list(request):
    return render(request, "prov_list.html")