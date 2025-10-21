from django.shortcuts import render

# Create your views here.
def mov_list(request):
    return render(request, "mov_list.html")