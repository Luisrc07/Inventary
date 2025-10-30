# En usuario/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # <--- ¡ESTA LÍNEA FALTABA!

app_name = 'usuario'

urlpatterns = [
    # URLs de autenticación de Django
    path('login/', auth_views.LoginView.as_view(template_name='usuario/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # URL para tu vista de registro
    path('registrar/', views.RegistroUsuarioView.as_view(), name='registrar'),

    path('lista/', views.UserListView.as_view(), name='user_list'),
    path('editar/<int:pk>/', views.UserUpdateView.as_view(), name='user_update'),
]