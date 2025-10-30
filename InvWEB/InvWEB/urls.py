"""
URL configuration for InvWEB project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from usuario import views as usuario_views

urlpatterns = [
    path('', usuario_views.root_redirect_view, name='root_redirect'),
    path('admin/', admin.site.urls),
    path('core/', include('core.urls')),
    path('inventario/', include('inventarioAPP.urls')),
    path('departamento/', include('departamentoAPP.urls')),
    path('movimiento/', include('movimientoAPP.urls')),
    path('proveedor/', include('proveedorAPP.urls')),
    path('usuario/', include('usuario.urls')),
    
]
