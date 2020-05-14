
import os
import zipfile

import boto3
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin

from pruebas_app.models import ResultadoVRT, Solicitud, Estrategia, Dispositivo, Version, Resultado
from pruebas_automaticas import settings


PROCESAR_PARA = 'Id del resultado a procesar para %s'

SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_CALABASH = SQS.get_queue_by_name(QueueName=settings.SQS_CALABASH_NAME)
COLA_CYPRESS = SQS.get_queue_by_name(QueueName=settings.SQS_CYPRESS_NAME)
COLA_PUPPETEER = SQS.get_queue_by_name(QueueName=settings.SQS_PUPPETEER_NAME)
COLA_MONKEY_MOVIL = SQS.get_queue_by_name(QueueName=settings.SQS_MONKEY_MOVIL_NAME)
COLA_CUCUMBER = SQS.get_queue_by_name(QueueName=settings.SQS_CUCUMBER_NAME)


def home(request):
    solicitudes = Solicitud.objects.filter(mutante=None).order_by('-id')
    paginator = Paginator(solicitudes, 10)  # Show 10 solicitudes per page
    page = request.GET.get('page')
    solicitudes_out = paginator.get_page(page)
    return render(request, 'pruebas_app/index.html', {'solicitudes': solicitudes_out})


def lanzar_estrategia(request):
    if request.method == 'GET':
        estrategias = Estrategia.objects.all()
        return render(request, 'pruebas_app/lanzar_estrategia.html', {'estrategias': estrategias})
    elif request.method == 'POST':
        solicitud = Solicitud()
        print('solicitud POST', request.POST)
        if 'solicitud_VRT' in request.POST:
            setup_vrt(request, solicitud)
        estrategia = Estrategia.objects.get(id=int(request.POST['estrategia']))
        if estrategia.aplicacion.tipo.tipo == settings.TIPOS_APLICACION['movil']:
            solicitud.dispositivo = Dispositivo.objects.get(id=int(request.POST['dispositivo']))
        solicitud.estrategia = estrategia
        solicitud.version = Version.objects.get(id=int(request.POST['version']))
        solicitud.save()
        tipo_aplicacion = estrategia.aplicacion.tipo.tipo

        for prueba in estrategia.prueba_set.all():
            tipo_prueba = prueba.tipo.nombre
            resultado = Resultado()
            resultado.solicitud = solicitud
            resultado.prueba = prueba
            resultado.save()
            herramienta = prueba.herramienta.nombre
            if tipo_prueba == settings.TIPOS_PRUEBAS["e2e"]:
                # Aquí se debe mandar el mensaje a la cola respectiva (por ahora voy a lanzar el proceso manual)
                if herramienta == settings.TIPOS_HERRAMIENTAS["cypress"]:
                    enviar_mensaje_cola(COLA_CYPRESS, herramienta, resultado)
                elif herramienta == 'Protractor':
                    pass
                elif herramienta == settings.TIPOS_HERRAMIENTAS["puppeteer"]:
                    enviar_mensaje_cola(COLA_PUPPETEER, herramienta, resultado)
                elif herramienta == settings.TIPOS_HERRAMIENTAS["calabash"]:
                    enviar_mensaje_cola(COLA_CALABASH, herramienta, resultado)
                elif herramienta == settings.TIPOS_HERRAMIENTAS["cucumber"]:
                    enviar_mensaje_cola(COLA_CUCUMBER, herramienta, resultado)
            elif tipo_prueba == settings.TIPOS_PRUEBAS["aleatorias"]:
                if tipo_aplicacion == settings.TIPOS_APLICACION['movil']:
                    enviar_mensaje_cola(COLA_MONKEY_MOVIL, herramienta, resultado)
                elif tipo_aplicacion == settings.TIPOS_APLICACION['web']:
                    enviar_mensaje_cola(COLA_CYPRESS, herramienta, resultado)
    return HttpResponseRedirect(reverse('home'))


def construir_message_attributes(resultado):
    return {
        'Id': {
            'StringValue': str(resultado.id),
            'DataType': 'Number'
        }
    }


def enviar_mensaje_cola(cola, herramienta, resultado):
    message = PROCESAR_PARA + herramienta
    cola.send_message(MessageBody=message,
                      MessageAttributes=construir_message_attributes(resultado))


def setup_vrt(request, solicitud):
    id_solicitud_vrt = request.POST['solicitud_VRT']
    sensibilidad_vrt = request.POST['sensibilidad_VRT']
    solicitud_vrt = Solicitud.objects.get(id=id_solicitud_vrt)
    solicitud.solicitud_VRT = solicitud_vrt
    solicitud.sensibilidad_VRT = sensibilidad_vrt


def condiciones_de_lanzamiento(request, estrategia_id):
    estrategia = Estrategia.objects.get(id=estrategia_id)
    # Mostrar solo solicitudes existentes que haya tenido la misma aplicación que se esta intentando lanzar
    dispositivos = Dispositivo.objects.all()
    solicitudes = Solicitud.objects.filter(estrategia=estrategia).order_by('-id')

    return render(request, 'pruebas_app/condiciones_de_lanzamiento.html',
                  {'solicitudes': solicitudes, 'estrategia': estrategia, 'dispositivos': dispositivos})


def descargar_evidencias(solicitud_id):
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
        elif r.prueba.herramienta.nombre == settings.TIPOS_HERRAMIENTAS["cucumber"]:
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
