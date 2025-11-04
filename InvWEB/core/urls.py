from django.urls import path
from core.views import DashboardView


app_name = 'core' 
urlpatterns = [
    
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]