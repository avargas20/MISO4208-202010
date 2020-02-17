from django.urls import path
from . import views
from django.conf.urls import url
from django.conf import settings

urlpatterns = [
    url(r'^$', views.home, name='home'),
    path('agregar_estrategia/', views.agregar_estrategia, name='agregar_estrategia'),
    path('lanzar_estrategia/', views.lanzar_estrategia, name='lanzar_estrategia'),
    path('obtener_versiones_de_una_estrategia/', views.obtener_versiones_de_una_estrategia, name='obtener_versiones_de_una_estrategia'),
]