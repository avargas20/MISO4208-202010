import json
import logging
import os
import subprocess
import zipfile

import boto3
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin

from pruebas_app.models import Aplicacion, Prueba, Version, Herramienta, Tipo, Estrategia, Solicitud, TipoAplicacion, \
    Dispositivo, ResultadoVRT, Operador, Mutacion
from pruebas_automaticas import settings

# Create your views here.

LOGGER = logging.getLogger(__name__)
SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_MUTACION = SQS.get_queue_by_name(QueueName=settings.SQS_MUTACION_NAME)


def home(request):
    solicitudes = Solicitud.objects.filter(mutante=None).order_by('-id')
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
    return lanzar_estrategia(request)


def agregar_prueba(request, estrategia_id):
    estrategia = Estrategia.objects.get(id=estrategia_id)
    herramientas = Herramienta.objects.all()
    tipos = Tipo.objects.all()
    pruebas = Prueba.objects.filter(estrategia=estrategia)
    return render(request, 'pruebas_app/agregar_prueba.html',
                  {'aplicacion': estrategia.aplicacion, 'estrategia': estrategia,
                   'herramientas': herramientas, 'tipos': tipos, 'pruebas': pruebas})


def eliminar_prueba(request, prueba_id):
    prueba = Prueba.objects.get(id=prueba_id)
    estrategia_id = prueba.estrategia.id
    prueba.delete()
    return agregar_prueba(request, estrategia_id)


def lanzar_estrategia(request):
    estrategias = Estrategia.objects.all()
    return render(request, 'pruebas_app/lanzar_estrategia.html', {'estrategias': estrategias})


def ver_estrategia(request):
    estrategias = Estrategia.objects.all()
    return render(request, 'pruebas_app/lanzar_estrategia.html', {'estrategias': estrategias})


def condiciones_de_lanzamiento(request, estrategia_id):
    estrategia = Estrategia.objects.get(id=estrategia_id)
    # Mostrar solo solicitudes existentes que haya tenido la misma aplicación que se esta intentando lanzar
    dispositivos = Dispositivo.objects.all()
    solicitudes = Solicitud.objects.filter(estrategia=estrategia).order_by('-id')

    return render(request, 'pruebas_app/condiciones_de_lanzamiento.html',
                  {'solicitudes': solicitudes, 'estrategia': estrategia, 'dispositivos': dispositivos})


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
            # Para sacar archivos adjuntos de un input file se hace accediendo a FILES del request y como es una lista
            # se saca el primero porque en el html solo dejamos esocger uno
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
            # este print('nombre paquete', salida.stdout.decode('utf-8')) imprime esto: package:
            # name='org.quantumbadger.redreader' versionCode='87' versionName='1.9.10' compileSdkVersion='28'
            # compileSdkVersionCodename='9'
            salida = salida.stdout.decode('utf-8')
            # Para obtener el nombre del paquete hago split por espacio, luego por = y luego quito las comillas simples
            # restantes
            nombre_paquete = salida.split()[1].split("=")[1].replace("'", "")
            version.nombre_paquete = nombre_paquete
            version.save()

        return HttpResponseRedirect(reverse('nueva_aplicacion'))


def eliminar_version(request, version_id):
    version = Version.objects.get(id=version_id)
    version.delete()
    return HttpResponseRedirect(reverse('nueva_aplicacion'))


@xframe_options_sameorigin
def ver_resultados(request, solicitud_id):
    try:
        solicitud = Solicitud.objects.get(id=int(solicitud_id))
    except Solicitud.DoesNotExist:
        raise Http404("Solicitud no encontrada")
    resultados = solicitud.resultado_set.all()
    videos = []
    logs = []
    screen_shots = []
    pag_html = []
    for r in resultados:
        if r.prueba.herramienta.nombre == settings.TIPOS_HERRAMIENTAS["cypress"]:
            videos.append(r)
            print(r.resultado.path)
        elif r.prueba.herramienta.nombre == settings.TIPOS_HERRAMIENTAS["calabash"] or r.prueba.tipo.nombre == \
                settings.TIPOS_PRUEBAS['aleatorias']:
            logs.append(r)
        elif r.prueba.herramienta.nombre == settings.TIPOS_HERRAMIENTAS["puppeteer"]:
            pag_html.append(r)
        elif r.prueba.herramienta.nombre == settings.TIPOS_HERRAMIENTAS["cucumber"] or r.prueba.herramienta.nombre == \
                settings.TIPOS_HERRAMIENTAS["generacion"]:
            print("El resultado es:", r.resultado.path)
            with zipfile.ZipFile(r.resultado.path, 'r') as zip_ref:
                zip_ref.extractall('archivos/resultados/extract/' + r.resultado.__str__())
            r.resultado = 'resultados/extract/' + r.resultado.__str__() + '/index.html'
            pag_html.append(r)
        if r.screenshot_set.all():
            screen_shots.append({'filename': r.prueba.filename, 'imagenes': r.screenshot_set.all()})
    imagenes_vrt = ResultadoVRT.objects.filter(solicitud=solicitud)

    return render(request, 'pruebas_app/ver_resultados.html',
                  {'solicitud': solicitud, 'videos': videos, 'logs': logs, 'imagenes_VRT': imagenes_vrt,
                   'screen_shots': screen_shots, 'pag_html': pag_html})


def obtener_versiones_de_una_aplicacion(request):
    aplicacion_id = int(request.GET['aplicacion_id'])
    result_set = []
    aplicacion = Aplicacion.objects.get(id=aplicacion_id)
    versiones = Version.objects.filter(aplicacion=aplicacion)
    for version in versiones:
        result_set.append({'numero': version.numero, 'id': version.id})
    return HttpResponse(json.dumps(result_set), content_type='application/json')


def mutacion(request):
    aplicaciones = Aplicacion.objects.filter(tipo__tipo=settings.TIPOS_APLICACION2.Movil.value)
    operadores = Operador.objects.all()
    return render(request, 'pruebas_app/mutacion.html', {'aplicaciones': aplicaciones, 'operadores': operadores})


def guardar_mutacion(request):
    if request.method == 'POST':
        numero_mutantes = request.POST['numero_mutantes']
        version = Version.objects.get(id=int(request.POST['version']))
        mutacion_version = Mutacion(version=version, numero_mutantes=numero_mutantes)
        mutacion_version.save()
        ids_operadores = request.POST.getlist('operadores')
        for id_operador in ids_operadores:
            mutacion_version.operadores.add(Operador.objects.get(id=id_operador))
        COLA_MUTACION.send_message(MessageBody='Id de la mutacion a procesar',
                                   MessageAttributes={
                                       'Id': {
                                           'StringValue': str(mutacion_version.id),
                                           'DataType': 'Number'
                                       }
                                   })
        return HttpResponseRedirect(reverse('ver_mutaciones'))

def ver_mutaciones(request):
    mutaciones = Mutacion.objects.all().order_by('-id')
    paginator = Paginator(mutaciones, 10)  # Show 10 mutaciones per page
    page = request.GET.get('page')
    mutaciones_out = paginator.get_page(page)
    return render(request, 'pruebas_app/ver_mutaciones.html', {'mutaciones': mutaciones_out})
