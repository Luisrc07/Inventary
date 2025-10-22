from django.urls import path
from inventarioAPP import views

app_name = 'inventarioAPP'

urlpatterns = [
    #url categoria
    path('categoria/', views.CategoriaListview.as_view(), name= 'categoria_list'),
    path('categoria/crear/', views.CategoriaCreateView.as_view(), name= 'categoria_crear'),
    path('categoria/editar/<uuid:pk>/', views.CategoriaUpdateView.as_view(), name= 'categoria_editar'),
    path('categoria/eliminar/<uuid:pk>/', views.CategoriaDeleteView.as_view(), name= 'categoria_eliminar'),

    #url producto
    path('producto/', views.ProductoListview.as_view(),name= 'producto_list'),
    path('producto/crear/', views.ProductoCreateView.as_view(), name= 'producto_crear'),
    path('producto/editar/<uuid:pk>/', views.ProductoUpdateView.as_view(), name= 'producto_editar'),
    path('producto/eliminar/<uuid:pk>/', views.ProductoDeleteView.as_view(), name= 'producto_eliminar'),

]