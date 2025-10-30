# departamentoAPP/urls.py

from django.urls import path
from departamentoAPP import views

app_name = 'departamentoAPP'

urlpatterns = [

     # --- URLs de Departamento ---
        # path('departamento/', ...) SE CONVIERTE EN path('', ...)
    path('', views.DepartamentoListView.as_view(), name= 'departamento_list'),
    path('crear/', views.DepartamentoCreateView.as_view(), name= 'departamento_crear'),
    path('editar/<uuid:pk>/', views.DepartamentoUpdateView.as_view(), name= 'departamento_editar'),
    path('eliminar/<uuid:pk>/', views.DepartamentoDeleteView.as_view(), name= 'departamento_eliminar'),

 # --- URLs de Encargado ---
        # Estas rutas están bien, ya que colgarán de 'departamento/'
   # path('encargado/', views.EncargadoListview.as_view(), name= 'encargado_list'),
   # path('encargado/crear/', views.EncargadoCreateView.as_view(), name= 'encargado_crear'),
   # path('encargado/editar/<uuid:pk>/', views.EncargadoUpdateView.as_view(), name= 'encargado_editar'),
        # Añadí la barra final (/) por consistencia
   #  path('encargado/eliminar/<uuid:pk>/', views.EncargadoDeleteView.as_view(), name= 'encargado_eliminar'), 

]