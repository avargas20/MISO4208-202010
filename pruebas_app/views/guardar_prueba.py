import os

from common import util
from pruebas_app.models import Prueba, Herramienta, Tipo, Estrategia
from pruebas_app.views.base import agregar_prueba
from pruebas_automaticas import settings


def guardar_prueba(request, estrategia_id):
    if request.method == 'POST':
        estrategia = Estrategia.objects.get(id=estrategia_id)
        tipo = Tipo.objects.get(id=request.POST['tipo'])
        # Si el tipo es E2E necesitamos el script y la herramienta
        # Si el tipo es aleatorio no se necesita nada mas
        tipo_prueba = tipo.nombre
        if tipo_prueba == settings.TIPOS_PRUEBAS["e2e"]:
            guardar_e2e(estrategia, request, tipo)
        elif tipo_prueba == settings.TIPOS_PRUEBAS["aleatorias"]:
            guardar_aleatorias(estrategia, request, tipo)
        else:
            raise Exception("Este %s no es soportado por la aplicación", tipo_prueba)
        return agregar_prueba(request, estrategia_id)


def guardar_e2e(estrategia, request, tipo):
    files = request.FILES.getlist('archivo')
    print("Los archivos recibidos son:", files)
    herramienta = Herramienta.objects.get(id=request.POST['herramienta'])
    print("La herramienta es", herramienta)
    if herramienta.__str__() == settings.TIPOS_HERRAMIENTAS["cucumber"]:
        for script in files:
            if os.path.splitext(script.name)[1] != '.feature':
                print("Uno de los archivos cargados no es .feature, se copiará al destino adecuado.")
                util.guardar_steps(script)
            else:
                crear_prueba_para_script(estrategia, herramienta, script, tipo)
    elif herramienta.__str__() == settings.TIPOS_HERRAMIENTAS["generacion"]:
        valores = {'nombre': 'name'}  # request.FILES.getlist('valores')
        cantidad = 10  # request.FILES.getlist('cantidad')
        for script in files:
            if os.path.splitext(script.name)[1] != '.feature':
                print("Uno de los archivos cargados no es .feature, se copiará al destino adecuado.")
                util.generar_tabla(script, cantidad, valores)
            else:
                crear_prueba_para_script(estrategia, herramienta, script, tipo)
    else:
        for script in files:
            crear_prueba_para_script(estrategia, herramienta, script, tipo)


def crear_prueba_para_script(estrategia, herramienta, script, tipo):
    prueba = Prueba()
    prueba.estrategia = estrategia
    prueba.tipo = tipo
    prueba.script = script
    prueba.herramienta = herramienta
    prueba.save()
    print(prueba)


def guardar_aleatorias(estrategia, request, tipo):
    prueba = Prueba()
    prueba.estrategia = estrategia
    prueba.tipo = tipo
    if prueba.estrategia.aplicacion.tipo.tipo == settings.TIPOS_APLICACION["web"]:
        prueba.script = "Monkey.js"
        prueba.herramienta = Herramienta.objects.get(nombre=settings.TIPOS_HERRAMIENTAS["cypress"])
    if prueba.estrategia.aplicacion.tipo.tipo == settings.TIPOS_APLICACION2.Movil.value:
        # la variable creada retorna un boolean indicando si el valor fue creado o no
        herramienta, creada = Herramienta.objects.get_or_create(nombre=settings.TIPOS_HERRAMIENTAS2.ADB.value,
                                                                defaults={
                                                                    'descripcion': 'Pruebas aleatorias móviles'})
        prueba.herramienta = herramienta
    prueba.numero_eventos = request.POST['numero_eventos']
    prueba.semilla = request.POST['semilla']
    prueba.save()
