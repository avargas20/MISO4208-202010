from django.conf.urls import url
from django.urls import path

from pruebas_app import views

urlpatterns = [
    url(r'^$', views.home, name='home'),

    path('aplicaciones/', views.aplicaciones, name='aplicaciones'),
    path('aplicaciones/<int:aplicacion_id>/', views.eliminar_aplicacion, name='eliminar_aplicacion'),
    path('aplicaciones/<int:aplicacion_id>/versiones/', views.aplicaciones_versiones, name='aplicaciones_versiones'),
    path('aplicaciones/<int:aplicacion_id>/versiones/<int:version_id>/', views.eliminar_version,
         name='eliminar_version'),

    path('obtener_versiones_de_una_aplicacion/', views.obtener_versiones_de_una_aplicacion,
         name='obtener_versiones_de_una_aplicacion'),

    path('estrategias/', views.estrategias, name='estrategias'),
    path('estrategias/<int:estrategia_id>/pruebas/', views.estrategias_pruebas, name='agregar_prueba'),
    path('estrategias/<int:estrategia_id>/condiciones/', views.condiciones_de_lanzamiento,
         name='condiciones_de_lanzamiento'),
    path('estrategias/lanzamientos/', views.lanzar_estrategia, name='lanzar_estrategia'),

    path('eliminar_prueba/<int:prueba_id>', views.eliminar_prueba, name='eliminar_prueba'),
    path('eliminar_estrategia/<int:estrategia_id>', views.eliminar_estrategia, name='eliminar_estrategia'),

    path('solicitudes/<int:solicitud_id>/evidencias/', views.descargar_evidencias, name='descargar_evidencias'),
    path('solicitudes/<int:solicitud_id>/resultados/', views.ver_resultados, name='ver_resultados'),

    path('configurar_cucumber/<int:estrategia_id>', views.configurar_cucumber, name='configurar_cucumber'),
    path('guardar_configuracion_cucumber/<int:estrategia_id>', views.guardar_configuracion_cucumber,
         name='guardar_configuracion_cucumber'),

    path('mutacion/', views.crear_mutacion, name='mutacion'),
    path('mutaciones/', views.ver_mutaciones, name='ver_mutaciones'),
    path('mutaciones/<int:mutacion_id>/evidencias/', views.descargar_evidencias_mutacion,
         name='descargar_evidencias_mutacion'),
    path('mutaciones/<int:mutacion_id>/resultados/', views.ver_resultados_mutacion, name='ver_resultados_mutacion'),
    path('mutaciones/<int:mutacion_id>/mutantes/', views.mutacion_mutantes, name='mutacion_mutantes'),
    path('mutaciones/<int:mutacion_id>/mutantes/<int:mutante_id>', views.mutacion_mutante_solicitud,
         name='mutacion_mutante_solicitud'),

]
