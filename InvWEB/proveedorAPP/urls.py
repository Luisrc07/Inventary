from django.urls import path
from proveedorAPP import views

app_name = 'proveedorAPP' 
urlpatterns = [
    path('proveedor/', views.ProveedorListview.as_view(), name= 'prov_list'),
    path('proveedor/crear/', views.ProveedorCreateView.as_view(), name= 'prov_crear'),
    path('proveedor/editar/<uuid:pk>/', views.ProveedorUpdateView.as_view(), name= 'prov_editar'),
    path('proveedor/eliminar/<uuid:pk>/', views.ProveedorDeleteView.as_view(), name= 'prov_eliminar'),
]