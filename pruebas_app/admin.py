from django.contrib import admin
from .models import Aplicacion, Version, Estrategia, Herramienta, Tipo, Prueba, Estado, Solicitud

# Register your models here.
admin.site.register(Aplicacion)
admin.site.register(Version)
admin.site.register(Estrategia)
admin.site.register(Herramienta)
admin.site.register(Tipo)
admin.site.register(Prueba)
admin.site.register(Estado)
admin.site.register(Solicitud)