from django.urls import path
from movimientoAPP import views

app_name = 'movimientoAPP' 
urlpatterns = [
    #url movimientos
    path('movimiento/', views.MovimientoListview.as_view(), name= 'movimiento_list'),
    path('movimiento/crear/', views.MovimientoCreateView.as_view(), name= 'movimiento_crear'),
    path('movimiento/editar/<uuid:pk>/', views.MovimientoUpdateView.as_view(), name= 'movimiento_editar'),
    path('movimiento/eliminar/<uuid:pk>/', views.MovimientoDeleteView.as_view(), name= 'movimiento_eliminar'),

    #url stock
    path('stock/', views.StockListview.as_view(),name= 'stock_list'),
    path('stock/crear/', views.StockCreateView.as_view(), name= 'stock_crear'),
    path('stock/editar/<uuid:pk>/', views.StockUpdateView.as_view(), name= 'stock_editar'),
    path('stock/eliminar/<uuid:pk>/', views.StockDeleteView.as_view(), name= 'stock_eliminar'),
    
]