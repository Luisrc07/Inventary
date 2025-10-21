from django.urls import path
from departamentoAPP import views

app_name = 'departamentoAPP'

urlpatterns = [
    path('lista/', views.departamento_list, name= 'departamento_list'),
    
]