from django.urls import path
from inventarioAPP import views

app_name = 'inventarioAPP'

urlpatterns = [
    path('producto_list/', views.producto_list, name= 'producto_list'),
    
]