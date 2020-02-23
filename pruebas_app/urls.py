from django.urls import path
from . import views
from django.conf.urls import url
from django.conf import settings

urlpatterns = [
    url(r'^$', views.home, name='home'),
    path('agregar_estrategia/', views.agregar_estrategia, name='agregar_estrategia'),
    path('lanzar_estrategia/', views.lanzar_estrategia, name='lanzar_estrategia'),
    path('obtener_versiones_de_una_estrategia/', views.obtener_versiones_de_una_estrategia, name='obtener_versiones_de_una_estrategia'),
    path('guardar_estrategia/', views.guardar_estrategia, name='guardar_estrategia'),
    path('agregar_scripts/<int:estrategia_id>', views.agregar_prueba, name='agregar_scripts'),
    path('guardar_prueba/<int:estrategia_id>', views.guardar_prueba, name='guardar_prueba'),
    path('eliminar_prueba/<int:prueba_id>', views.eliminar_prueba, name='eliminar_prueba'),
    path('eliminar_estrategia/<int:estrategia_id>', views.eliminar_estrategia, name='eliminar_estrategia'),
]