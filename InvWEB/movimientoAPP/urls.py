from django.urls import path
from movimientoAPP import views

app_name = 'movimientoAPP' 
urlpatterns = [
    #url movimientos
    path('movimiento/', views.MovimientoListview.as_view(), name= 'movimiento_list'),
    path('movimiento/crear/', views.MovimientoCreateView.as_view(), name= 'movimiento_crear'),
    path('movimiento/editar/<uuid:pk>/', views.MovimientoUpdateView.as_view(), name= 'movimiento_editar'),
   

    #url stock
path('stock/', views.StockGroupedListview.as_view(), name='stock_list_grouped'),    
    
]