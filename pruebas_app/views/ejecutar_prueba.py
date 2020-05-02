import boto3
from django.http import HttpResponseRedirect
from django.urls import reverse

from pruebas_app.models import Version, Estrategia, Solicitud, Resultado, Dispositivo
from pruebas_automaticas import settings

PROCESAR_PARA = 'Id del resultado a procesar para %s'

SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_CALABASH = SQS.get_queue_by_name(QueueName=settings.SQS_CALABASH_NAME)
COLA_CYPRESS = SQS.get_queue_by_name(QueueName=settings.SQS_CYPRESS_NAME)
COLA_PUPPETEER = SQS.get_queue_by_name(QueueName=settings.SQS_PUPPETEER_NAME)
COLA_MONKEY_MOVIL = SQS.get_queue_by_name(QueueName=settings.SQS_MONKEY_MOVIL_NAME)
COLA_CUCUMBER = SQS.get_queue_by_name(QueueName=settings.SQS_CUCUMBER_NAME)


def ejecutar_estrategia(request):
    if request.method == 'POST':
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
                elif (herramienta == settings.TIPOS_HERRAMIENTAS["cucumber"]) :
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


def enviar_mensaje_cola(COLA, herramienta, resultado):
    message = PROCESAR_PARA + herramienta
    COLA.send_message(MessageBody=message,
                      MessageAttributes=construir_message_attributes(resultado))


def setup_vrt(request, solicitud):
    id_solicitud_vrt = request.POST['solicitud_VRT']
    sensibilidad_vrt = request.POST['sensibilidad_VRT']
    solicitud_vrt = Solicitud.objects.get(id=id_solicitud_vrt)
    solicitud.solicitud_VRT = solicitud_vrt
    solicitud.sensibilidad_VRT = sensibilidad_vrt
