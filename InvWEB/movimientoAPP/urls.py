from django.urls import path
from movimientoAPP import views

app_name = 'movimientoAPP' 
urlpatterns = [
    path('lista/', views.mov_list, name= 'mov_list'),
     
]