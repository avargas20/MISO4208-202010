import json
import os
import threading
import logging
import subprocess
import boto3
from django.core.files import File
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.urls import reverse

from common import worker_cypress, worker_monkey_movil, worker_calabash, util
from pruebas_automaticas import settings
from .models import Aplicacion, Prueba, Version, Herramienta, Tipo, Estrategia, Solicitud, Resultado, TipoAplicacion

# Create your views here.

LOGGER = logging.getLogger(__name__)
SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_CALABASH = SQS.get_queue_by_name(QueueName=settings.SQS_CALABASH_NAME)
COLA_CYPRESS = SQS.get_queue_by_name(QueueName=settings.SQS_CYPRESS_NAME)
COLA_MONKEY_MOVIL = SQS.get_queue_by_name(QueueName=settings.SQS_MONKEY_MOVIL_NAME)


def home(request):
    solicitudes = Solicitud.objects.all().order_by('-id')
    paginator = Paginator(solicitudes, 10)  # Show 10 solicitudes per page
    page = request.GET.get('page')
    solicitudes_out = paginator.get_page(page)
    return render(request, 'pruebas_app/index.html', {'solicitudes': solicitudes_out})


def agregar_estrategia(request):
    aplicaciones = Aplicacion.objects.all()
    herramientas = Herramienta.objects.all()
    tipos = Tipo.objects.all()
    return render(request, 'pruebas_app/agregar_estrategia.html',
                  {'aplicaciones': aplicaciones, 'herramientas': herramientas, 'tipos': tipos})


def guardar_estrategia(request):
    if request.method == 'POST':
        print(request.POST)
        version = Version.objects.get(id=request.POST['versiones'])
        nombre_estrategia = request.POST['nombre_estrategia']
        descripcion_estrategia = request.POST['descripcion_estrategia']
        estrategia = Estrategia(
            nombre=nombre_estrategia, descripcion=descripcion_estrategia, version=version)
        estrategia.save()
        return HttpResponseRedirect(reverse('agregar_prueba', args=(estrategia.id,)))


def eliminar_estrategia(request, estrategia_id):
    estrategia = Estrategia.objects.get(id=estrategia_id)
    estrategia.delete()
    return lanzar_estrategia(request)


def agregar_prueba(request, estrategia_id):
    estrategia = Estrategia.objects.get(id=estrategia_id)
    herramientas = Herramienta.objects.all()
    tipos = Tipo.objects.all()
    pruebas = Prueba.objects.filter(estrategia=estrategia)
    return render(request, 'pruebas_app/agregar_prueba.html',
                  {'aplicacion': estrategia.version.aplicacion, 'version': estrategia.version, 'estrategia': estrategia,
                   'herramientas': herramientas, 'tipos': tipos, 'pruebas': pruebas})


def guardar_prueba(request, estrategia_id):
    if request.method == 'POST':
        tipo = Tipo.objects.get(id=request.POST['tipo'])
        estrategia = Estrategia.objects.get(id=estrategia_id)
        tipo_aplicacion = estrategia.version.aplicacion.tipo.tipo
        herramienta = Herramienta.objects.get(
            id=request.POST['herramienta'])
        # Si el tipo es E2E necesitamos el script y la herramienta
        if tipo.nombre == settings.TIPOS_PRUEBAS["e2e"]:
            _, script = request.FILES.popitem()
            script = script[0]
            prueba = Prueba(script=script, herramienta=herramienta,
                            tipo=tipo, estrategia=estrategia)
        elif tipo.nombre == settings.TIPOS_PRUEBAS["aleatorias"]:
            # Si el tipo es random y movil no necesitamos nada mas
            if tipo_aplicacion == settings.TIPOS_APLICACION["movil"]:
                prueba = Prueba(tipo=tipo, estrategia=estrategia)
            # Si el tipo es random y web no necesitamos el script
            elif tipo_aplicacion == settings.TIPOS_APLICACION["web"]:
                prueba = Prueba(herramienta=herramienta,
                                tipo=tipo, estrategia=estrategia)
                prueba.save()
                util.reemplazar_token_con_url(prueba)
        print(prueba)
        prueba.save()

        print(request.POST)
        print(request.FILES)
        return agregar_prueba(request, estrategia_id)


def eliminar_prueba(request, prueba_id):
    prueba = Prueba.objects.get(id=prueba_id)
    estrategia_id = prueba.estrategia.id
    prueba.delete()
    return agregar_prueba(request, estrategia_id)


def obtener_versiones_de_una_aplicacion(request):
    aplicacion_id = int(request.GET['aplicacion_id'])
    print("ajax aplicacion_id ", aplicacion_id)

    result_set = []
    versiones = []
    aplicacion = Aplicacion.objects.get(id=aplicacion_id)
    print("selected app name ", aplicacion)
    versiones = Version.objects.filter(aplicacion=aplicacion)
    for version in versiones:
        print("version number", version.numero)
        result_set.append({'numero': version.numero, 'id': version.id})
    return HttpResponse(json.dumps(result_set), content_type='application/json')


def lanzar_estrategia(request):
    estrategias = Estrategia.objects.all()
    return render(request, 'pruebas_app/lanzar_estrategia.html', {'estrategias': estrategias})


def ver_estrategia(request):
    estrategias = Estrategia.objects.all()
    return render(request, 'pruebas_app/lanzar_estrategia.html', {'estrategias': estrategias})


def condiciones_de_lanzamiento(request, estrategia_id):
    estrategia = Estrategia.objects.get(id=estrategia_id)
    # Mostrar solo solicitudes existentes que haya tenido la misma aplicacion que se esta intentando lanzar
    solicitudes = Solicitud.objects.filter(estrategia__version__aplicacion=estrategia.version.aplicacion).order_by(
        '-id')
    return render(request, 'pruebas_app/condiciones_de_lanzamiento.html',
                  {'solicitudes': solicitudes, 'estrategia': estrategia})


def ejecutar_estrategia(request, estrategia_id):
    solicitud = Solicitud()
    if request.method == 'POST':
        print('solicitud POST', request.POST)
        if 'solicitud_VRT' in request.POST:
            id_solicitud_VRT = request.POST['solicitud_VRT']
            solicitud_VRT = Solicitud.objects.get(id=id_solicitud_VRT)
            solicitud.solicitud_VRT = solicitud_VRT
    estrategia = Estrategia.objects.get(id=estrategia_id)
    solicitud.estrategia = estrategia
    solicitud.save()
    tipo_aplicacion = estrategia.version.aplicacion.tipo.tipo

    for prueba in estrategia.prueba_set.all():
        tipo_prueba = prueba.tipo.nombre
        resultado = Resultado()
        resultado.solicitud = solicitud
        resultado.prueba = prueba
        resultado.save()
        if tipo_prueba == settings.TIPOS_PRUEBAS["e2e"]:
            herramienta = prueba.herramienta.nombre
            # Aqui se debe mandar el mensaje a la cola respectiva (por ahora voy a lanzar el proceso manual)
            if herramienta == settings.TIPOS_HERRAMIENTAS["cypress"]:
                response = COLA_CYPRESS.send_message(MessageBody='Id del resultado a procesar para cypress',
                                                     MessageAttributes={
                                                         'Id': {
                                                             'StringValue': str(resultado.id),
                                                             'DataType': 'Number'
                                                         }
                                                     })
            elif herramienta == 'Protractor':
                pass
            elif herramienta == 'Pupperteer':
                pass
            elif herramienta == settings.TIPOS_HERRAMIENTAS["calabash"]:
                response = COLA_CALABASH.send_message(MessageBody='Id del resultado a procesar para calabash',
                                                      MessageAttributes={
                                                          'Id': {
                                                              'StringValue': str(resultado.id),
                                                              'DataType': 'Number'
                                                          }
                                                      })

        elif tipo_prueba == settings.TIPOS_PRUEBAS["aleatorias"]:
            if tipo_aplicacion == settings.TIPOS_APLICACION['movil']:
                response = COLA_MONKEY_MOVIL.send_message(MessageBody='Id del resultado a procesar para monkey movil',
                                                          MessageAttributes={
                                                              'Id': {
                                                                  'StringValue': str(resultado.id),
                                                                  'DataType': 'Number'
                                                              }
                                                          })
            elif tipo_aplicacion == settings.TIPOS_APLICACION['web']:
                response = COLA_CYPRESS.send_message(MessageBody='Id del resultado a procesar para monkey web',
                                                     MessageAttributes={
                                                         'Id': {
                                                             'StringValue': str(resultado.id),
                                                             'DataType': 'Number'
                                                         }
                                                     })
    return HttpResponseRedirect(reverse('home'))


def descargar_evidencias(request, solicitud_id):
    solicitud = Solicitud.objects.get(id=solicitud_id)
    file_path = solicitud.evidencia.path
    print("ruta buscada", file_path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type="application/")
            response['Content-Disposition'] = 'inline; filename=' + \
                                              os.path.basename(file_path)
            return response
    raise Http404


def nueva_aplicacion(request):
    aplicaciones = Aplicacion.objects.all()
    tipos = TipoAplicacion.objects.all()
    LOGGER.info(aplicaciones)
    return render(request, 'pruebas_app/nueva_aplicacion.html',
                  {'aplicaciones': aplicaciones, 'tipos': tipos})


def guardar_aplicacion(request):
    if request.method == 'POST':
        print(request.POST)
        nombre_aplicacion = request.POST['nombre_aplicacion']
        descripcion_aplicacion = request.POST['descripcion_aplicacion']
        tipo = request.POST['tipo']

        tipo_aplicacion = TipoAplicacion.objects.get(id=tipo)
        aplicacion = Aplicacion(
            nombre=nombre_aplicacion, descripcion=descripcion_aplicacion, tipo=tipo_aplicacion)
        aplicacion.save()
        return HttpResponseRedirect(reverse('nueva_aplicacion'))


def eliminar_aplicacion(request, aplicacion_id):
    aplicacion = Aplicacion.objects.get(id=aplicacion_id)
    aplicacion.delete()
    return nueva_aplicacion(request)


def agregar_version(request, aplicacion_id):
    versiones = Version.objects.filter(aplicacion=aplicacion_id)
    aplicacion = Aplicacion.objects.get(id=aplicacion_id)
    return render(request, 'pruebas_app/agregar_version.html',
                  {'versiones': versiones, 'aplicacion': aplicacion})


def guardar_version(request, aplicacion_id):
    if request.method == 'POST':
        print(request.POST)
        aplicacion = Aplicacion.objects.get(id=aplicacion_id)
        numero_version = request.POST['numero_version']
        descripcion_version = request.POST['descripcion_version']
        # Dependiendo del tipo de aplicacion se saca o el .apk (movil) o la url (web)
        if aplicacion.tipo.tipo == settings.TIPOS_APLICACION["web"]:
            url = request.POST['url_version']
            version = Version(
                numero=numero_version, descripcion=descripcion_version, aplicacion=aplicacion, url=url)
            version.save()
        elif aplicacion.tipo.tipo == settings.TIPOS_APLICACION["movil"]:
            # Para sacar archivos adjuntos de un input file se hace accediendo a FILES del request y como es una lista se saca el primero porque en el html solo dejamos esocger uno
            _, apk = request.FILES.popitem()
            apk = apk[0]
            version = Version(
                numero=numero_version, descripcion=descripcion_version, aplicacion=aplicacion, apk=apk)
            version.save()
            # Ejecuto el siguiente comando para obtener el nombre del paquete del apk
            salida = subprocess.run(['aapt', 'dump', 'badging', version.apk.path, '|', 'findstr', '-i', 'package:'],
                                    shell=True, check=False, cwd=os.path.join(settings.ANDROID_SDK,
                                                                              settings.RUTAS_INTERNAS_SDK_ANDROID[
                                                                                  'build-tools']),
                                    stdout=subprocess.PIPE)
            #
            # este print('nombre paquete', salida.stdout.decode('utf-8')) imprime esto: package: name='org.quantumbadger.redreader' versionCode='87' versionName='1.9.10' compileSdkVersion='28' compileSdkVersionCodename='9'
            salida = salida.stdout.decode('utf-8')
            # Para obtener el nombre del paquete hago split por espacio, luego por = y luego quito las comillas simples restantes
            nombre_paquete = salida.split()[1].split("=")[1].replace("'", "")
            version.nombre_paquete = nombre_paquete
            version.save()

        return HttpResponseRedirect(reverse('nueva_aplicacion'))


def eliminar_version(request, version_id):
    version = Version.objects.get(id=version_id)
    version.delete()
    return HttpResponseRedirect(reverse('nueva_aplicacion'))
