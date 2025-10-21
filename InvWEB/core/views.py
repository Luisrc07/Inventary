from django.shortcuts import render, HttpResponse
# Create your views here.

def base(request):
    return render(request, "base.html")


