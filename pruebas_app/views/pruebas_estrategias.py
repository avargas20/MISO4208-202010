import logging
import os

import boto3
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from common import util
from pruebas_app.models import Aplicacion
from pruebas_app.models import Prueba, Herramienta, Tipo, Estrategia
from pruebas_app.views.resultado_solicitud import lanzar_estrategia
from pruebas_automaticas import settings

# Create your views here.

LOGGER = logging.getLogger(__name__)
SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_MUTACION = SQS.get_queue_by_name(QueueName=settings.SQS_MUTACION_NAME)


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
        if herramienta.nombre == settings.TIPOS_HERRAMIENTAS["cucumber"] and request.POST.get('checkboxCucumber',
                                                                                              False) is False:
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
                    if request.POST['nombre_encabezado1'] and request.POST['tipo_dato1']:
                        valores[request.POST['nombre_encabezado1']] = request.POST['tipo_dato1']
                    if request.POST['nombre_encabezado2'] and request.POST['tipo_dato2']:
                        valores[request.POST['nombre_encabezado2']] = request.POST['tipo_dato2']
                    if request.POST['nombre_encabezado3'] and request.POST['tipo_dato3']:
                        valores[request.POST['nombre_encabezado3']] = request.POST['tipo_dato3']
                    if request.POST['nombre_encabezado4'] and request.POST['tipo_dato4']:
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
        prueba.semilla = request.POST['semilla']
        herramienta, creada = Herramienta.objects.get_or_create(nombre=settings.TIPOS_HERRAMIENTAS2.ADB.value,
                                                                defaults={
                                                                    'descripcion': 'Pruebas aleatorias móviles'})
        prueba.herramienta = herramienta
    prueba.numero_eventos = request.POST['numero_eventos']
    prueba.save()


def configurar_cucumber(request, estrategia_id):
    estrategia = Estrategia.objects.get(id=estrategia_id)
    return render(request, 'pruebas_app/configurar_cucumber.html',
                  {'estrategia': estrategia})


def guardar_configuracion_cucumber(request, estrategia_id):
    print(request)
    guardar_prueba(request, estrategia_id)
    return HttpResponseRedirect(reverse('agregar_prueba', args=[estrategia_id]))


def agregar_estrategia(request):
    aplicaciones = Aplicacion.objects.all()
    herramientas = Herramienta.objects.all()
    tipos = Tipo.objects.all()
    return render(request, 'pruebas_app/agregar_estrategia.html',
                  {'aplicaciones': aplicaciones, 'herramientas': herramientas, 'tipos': tipos})


def guardar_estrategia(request):
    if request.method == 'POST':
        print(request.POST)
        nombre_estrategia = request.POST['nombre_estrategia']
        descripcion_estrategia = request.POST['descripcion_estrategia']
        aplicacion = Aplicacion.objects.get(id=int(request.POST['aplicacion']))
        estrategia = Estrategia(
            nombre=nombre_estrategia, descripcion=descripcion_estrategia, aplicacion=aplicacion)
        estrategia.save()
        return HttpResponseRedirect(reverse('agregar_prueba', args=(estrategia.id,)))


def eliminar_estrategia(request, estrategia_id):
    estrategia = Estrategia.objects.get(id=estrategia_id)
    estrategia.delete()
    return HttpResponseRedirect(reverse('lanzar_estrategia'))


def agregar_prueba(request, estrategia_id):
    estrategia = Estrategia.objects.get(id=estrategia_id)
    herramientas = Herramienta.objects.all()
    tipos = Tipo.objects.all()
    pruebas = Prueba.objects.filter(estrategia=estrategia)
    return render(request, 'pruebas_app/agregar_prueba.html',
                  {'aplicacion': estrategia.aplicacion, 'estrategia': estrategia,
                   'herramientas': herramientas, 'tipos': tipos, 'pruebas': pruebas})


def detalle_estrategia(request, estrategia_id):
    estrategia = Estrategia.objects.get(id=estrategia_id)
    herramientas = Herramienta.objects.all()
    tipos = Tipo.objects.all()
    pruebas = Prueba.objects.filter(estrategia=estrategia)
    return render(request, 'pruebas_app/detalle_estrategia.html',
                  {'aplicacion': estrategia.aplicacion, 'estrategia': estrategia,
                   'herramientas': herramientas, 'tipos': tipos, 'pruebas': pruebas})


def copiar_estrategia(request, estrategia_id):
    estrategia_anterior = Estrategia.objects.get(id=estrategia_id)
    estrategia = estrategia_anterior
    estrategia.pk = None
    estrategia.save()
    estrategia.nombre = '%s_%s' % (estrategia.nombre, str(estrategia.pk))
    estrategia.save()

    pruebas_anteriores = Prueba.objects.filter(estrategia=estrategia_id)
    for p in pruebas_anteriores:
        prueba = p
        prueba.estrategia = estrategia
        prueba.pk = None
        prueba.save()
    return HttpResponseRedirect(reverse('agregar_prueba', args=(estrategia.id,)))


def eliminar_prueba(request, prueba_id):
    prueba = Prueba.objects.get(id=prueba_id)
    estrategia_id = prueba.estrategia.id
    prueba.delete()
    return agregar_prueba(request, estrategia_id)


def ver_estrategia(request):
    estrategias = Estrategia.objects.all()
    return render(request, 'pruebas_app/lanzar_estrategia.html', {'estrategias': estrategias})
