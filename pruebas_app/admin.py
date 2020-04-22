from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Aplicacion, Version, Estrategia, Herramienta, Tipo, Prueba, Solicitud, TipoAplicacion, Resultado, \
    Dispositivo, ResultadoVRT, ScreenShot, Mutante, Mutacion, Operador


class OperadorResource(resources.ModelResource):

    class Meta:
        model = Operador


class OperadorAdmin(ImportExportModelAdmin):
    resource_class = OperadorResource

# Register your models here.
admin.site.register(Aplicacion)
admin.site.register(Version)
admin.site.register(Estrategia)
admin.site.register(Herramienta)
admin.site.register(Tipo)
admin.site.register(Dispositivo)
admin.site.register(Prueba)
admin.site.register(Solicitud)
admin.site.register(TipoAplicacion)
admin.site.register(Resultado)
admin.site.register(ResultadoVRT)
admin.site.register(ScreenShot)
admin.site.register(Mutacion)
admin.site.register(Mutante)
admin.site.register(Operador, OperadorAdmin)
