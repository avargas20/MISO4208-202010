from django.contrib import admin

from .models import Aplicacion, Version, Estrategia, Herramienta, Tipo, Prueba, Estado, Solicitud, TipoAplicacion, \
    Resultado, ResultadoVRT, ScreenShot

# Register your models here.
admin.site.register(Aplicacion)
admin.site.register(Version)
admin.site.register(Estrategia)
admin.site.register(Herramienta)
admin.site.register(Tipo)
admin.site.register(Prueba)
admin.site.register(Estado)
admin.site.register(Solicitud)
admin.site.register(TipoAplicacion)
admin.site.register(Resultado)
admin.site.register(ResultadoVRT)
admin.site.register(ScreenShot)