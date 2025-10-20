from django.urls import path
from InvWEBAPP import views

urlpatterns = [
    path('', views.prueba, name= 'prueba')
   
]