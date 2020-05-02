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
    print("El request a guardar es:", request.POST)
    if request.FILES.getlist('archivo'):
        files = request.FILES.getlist('archivo')
        print("Los archivos recibidos son:", files)
        herramienta = Herramienta.objects.get(id=request.POST['herramienta'])
        print("La herramienta es", herramienta)
        if herramienta.nombre == settings.TIPOS_HERRAMIENTAS["cucumber"] and request.POST.get('checkboxCucumber', False) is False:
            for script in files:
                if os.path.splitext(script.name)[1] != '.feature':
                    print("Uno de los archivos cargados no es .feature, se copiará al destino adecuado.")
                    util.guardar_steps(script)
                else:
                    crear_prueba_para_script(estrategia, herramienta, script, tipo)
        elif herramienta.nombre == settings.TIPOS_HERRAMIENTAS["cucumber"] and request.POST['checkboxCucumber']:
            for script in files:
                if os.path.splitext(script.name)[1] != '.feature':
                    print("Uno de los archivos cargados no es .feature, se copiará al destino adecuado.")
                    util.guardar_steps(script)
                else:
                    valores = {}
                    print("Request con valores:", request)
                    if (request.POST['nombre_encabezado1'] and request.POST['tipo_dato1']):
                        valores[request.POST['nombre_encabezado1']] = request.POST['tipo_dato1']
                    if (request.POST['nombre_encabezado2'] and request.POST['tipo_dato2']):
                        valores[request.POST['nombre_encabezado2']] = request.POST['tipo_dato2']
                    if (request.POST['nombre_encabezado3'] and request.POST['tipo_dato3']):
                        valores[request.POST['nombre_encabezado3']] = request.POST['tipo_dato3']
                    if (request.POST['nombre_encabezado4'] and request.POST['tipo_dato4']):
                        valores[request.POST['nombre_encabezado4']] = request.POST['tipo_dato4']
                    print("iniciando proceso de generación de datos con valores:", valores)
                    cantidad = request.POST['numero_datos']
                    print("y cantidad:", cantidad)
                    archivo_generado = util.generar_tabla(files, cantidad, valores)
                    crear_prueba_para_script(estrategia, herramienta, archivo_generado, tipo)
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
