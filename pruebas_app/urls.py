from django.conf.urls import url
from django.urls import path

from pruebas_app import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    path('agregar_estrategia/', views.agregar_estrategia, name='agregar_estrategia'),
    path('obtener_versiones_de_una_aplicacion/', views.obtener_versiones_de_una_aplicacion,
         name='obtener_versiones_de_una_aplicacion'),
    path('lanzar_estrategia/', views.lanzar_estrategia, name='lanzar_estrategia'),
    path('nueva_aplicacion/', views.nueva_aplicacion, name='nueva_aplicacion'),
    path('guardar_estrategia/', views.guardar_estrategia, name='guardar_estrategia'),
    path('agregar_prueba/<int:estrategia_id>', views.agregar_prueba, name='agregar_prueba'),
    path('guardar_prueba/<int:estrategia_id>', views.guardar_prueba, name='guardar_prueba'),
    path('eliminar_prueba/<int:prueba_id>', views.eliminar_prueba, name='eliminar_prueba'),
    path('eliminar_estrategia/<int:estrategia_id>', views.eliminar_estrategia, name='eliminar_estrategia'),
    path('ejecutar_estrategia/', views.ejecutar_estrategia, name='ejecutar_estrategia'),
    path('ver_estrategias/', views.ver_estrategia, name='ver_estrategia'),
    path('descargar_evidencias/<int:solicitud_id>', views.descargar_evidencias, name='descargar_evidencias'),
    path('guardar_aplicacion/', views.guardar_aplicacion, name='guardar_aplicacion'),
    path('eliminar_aplicacion/<int:aplicacion_id>', views.eliminar_aplicacion, name='eliminar_aplicacion'),
    path('agregar_version/<int:aplicacion_id>', views.agregar_version, name='agregar_version'),
    path('configurar_cucumber/<int:estrategia_id>', views.configurar_cucumber, name='configurar_cucumber'),
    path('guardar_configuracion_cucumber/<int:estrategia_id>', views.guardar_configuracion_cucumber,
         name='guardar_configuracion_cucumber'),
    path('guardar_version/<int:aplicacion_id>', views.guardar_version, name='guardar_version'),
    path('eliminar_version/<int:version_id>', views.eliminar_version, name='eliminar_version'),
    path('condiciones_de_lanzamiento/<int:estrategia_id>', views.condiciones_de_lanzamiento,
         name='condiciones_de_lanzamiento'),
    path('ver_resultados/<int:solicitud_id>', views.ver_resultados, name='ver_resultados'),
    path('mutacion/', views.crear_mutacion, name='mutacion'),
    path('mutaciones/', views.ver_mutaciones, name='ver_mutaciones'),
    path('mutaciones/evidencias/<int:mutacion_id>', views.descargar_evidencias_mutacion, name='descargar_evidencias_mutacion'),
    path('mutaciones/<int:mutacion_id>', views.ver_resultados_mutacion, name='ver_resultados_mutacion'),
    path('mutaciones/<int:mutacion_id>/mutantes', views.mutacion_mutantes, name='mutacion_mutantes'),

]
