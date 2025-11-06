from django.urls import path
from movimientoAPP import views

app_name = 'movimientoAPP' 
urlpatterns = [

    path('inicio/', views.MovimientoListview.as_view(), name='inicio'),

    
    #url movimientos
    path('movimiento/', views.MovimientoListview.as_view(), name= 'movimiento_list'),
    path('movimiento/crear/', views.MovimientoCreateView.as_view(), name= 'movimiento_crear'),
    path('movimiento/editar/<uuid:pk>/', views.MovimientoUpdateView.as_view(), name= 'movimiento_editar'),
   
    path('ajax/load-productos/', views.load_productos, name='ajax_load_productos'),
    #url stock
    path('stock/', views.StockGroupedListview.as_view(), name='stock_list_grouped'),    
    path('stock/reporte/departamento/<uuid:pk>/pdf/', views.generar_reporte_stock_pdf, name='reporte_stock_departamento_pdf'), 

    path('ajax/load-categorias/', views.load_categorias, name='ajax_load_categorias'),
    path('ajax/get-stock-departamento/', views.get_stock_departamento, name='ajax_get_stock_departamento'),
]