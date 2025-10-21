from django.urls import path
from proveedorAPP import views

app_name = 'proveedorAPP' 
urlpatterns = [
    path('lista/', views.prov_list, name= 'prov_list'),
     
]