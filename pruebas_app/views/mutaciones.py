import zipfile
from io import BytesIO

import boto3
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from pruebas_app.models import Aplicacion, Version, Operador, Mutacion, Estrategia, Mutante, Solicitud, Dispositivo, \
    Resultado
from pruebas_automaticas import settings

SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_MUTACION = SQS.get_queue_by_name(QueueName=settings.SQS_MUTACION_NAME)
COLA_CALABASH = SQS.get_queue_by_name(QueueName=settings.SQS_CALABASH_NAME)
COLA_MONKEY_MOVIL = SQS.get_queue_by_name(QueueName=settings.SQS_MONKEY_MOVIL_NAME)
PROCESAR_PARA = 'Id del resultado a procesar para %s'


def crear_mutacion(request):
    if request.method == 'GET':
        aplicaciones = Aplicacion.objects.filter(tipo__tipo=settings.TIPOS_APLICACION2.Movil.value)
        operadores = Operador.objects.all()
        return render(request, 'pruebas_app/crear_mutacion.html',
                      {'aplicaciones': aplicaciones, 'operadores': operadores})
    elif request.method == 'POST':
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


def descargar_evidencias_mutacion(request, mutacion_id):
    mutacion = Mutacion.objects.get(id=mutacion_id)

    # Files (local path) to put in the .zip
    filenames = [mutacion.reporte_json, mutacion.reporte_csv, mutacion.reporte_log]

    stream = BytesIO()
    temp_zip_file = zipfile.ZipFile(stream, 'w')

    for f in filenames:
        temp_zip_file.write(f.path, f.name)

    temp_zip_file.close()

    response = HttpResponse(stream.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s' % '{0}_result_mutation.zip'.format(mutacion_id)

    return response


def ver_resultados_mutacion(request, mutacion_id):
    try:
        mutacion = Mutacion.objects.get(id=int(mutacion_id))
    except Mutacion.DoesNotExist:
        raise Http404("Mutación no encontrada")

    return render(request, 'pruebas_app/ver_resultados_mutacion.html', {'mutacion': mutacion})


def mutacion_mutantes(request, mutacion_id):
    # Cuando el metodo es GET mostramos los datos de la mutacion
    mutacion = get_object_or_404(Mutacion, pk=mutacion_id)
    if request.method == 'GET':
        estrategias = Estrategia.objects.filter(aplicacion=mutacion.version.aplicacion)
        return render(request, 'pruebas_app/mutacion_mutantes.html', {'mutacion': mutacion, 'estrategias': estrategias})
    # Cuando el metodo es POST creamos las solicitudes para todos los mutantes
    elif request.method == 'POST':
        dispositivo = Dispositivo.objects.get(id=1)
        estrategia = Estrategia.objects.get(id=int(request.POST['id_estrategia']))
        for mutante in mutacion.mutante_set.all():
            crear_solicitud(dispositivo, estrategia, mutante)
    return HttpResponseRedirect(reverse('mutacion_mutantes', args=[mutacion_id]))


def mutacion_mutante_solicitud(request, mutacion_id, mutante_id):
    if request.method == 'POST':
        dispositivo = Dispositivo.objects.get(id=1)
        estrategia = Estrategia.objects.get(id=int(request.POST['id_estrategia']))
        mutante = Mutante.objects.get(id=int(mutante_id))
        crear_solicitud(dispositivo, estrategia, mutante)
    return HttpResponseRedirect(reverse('mutacion_mutantes', args=[mutacion_id]))


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


def crear_solicitud(dispositivo, estrategia, mutante):
    solicitud = Solicitud()
    solicitud.dispositivo = dispositivo
    solicitud.estrategia = estrategia
    solicitud.mutante = mutante
    solicitud.save()
    tipo_aplicacion = solicitud.estrategia.aplicacion.tipo.tipo

    for prueba in solicitud.estrategia.prueba_set.all():
        tipo_prueba = prueba.tipo.nombre
        resultado = Resultado()
        resultado.solicitud = solicitud
        resultado.prueba = prueba
        resultado.save()
        herramienta = prueba.herramienta.nombre
        if tipo_prueba == settings.TIPOS_PRUEBAS["e2e"]:
            if herramienta == settings.TIPOS_HERRAMIENTAS["calabash"]:
                enviar_mensaje_cola(COLA_CALABASH, herramienta, resultado)
        elif tipo_prueba == settings.TIPOS_PRUEBAS["aleatorias"]:
            if tipo_aplicacion == settings.TIPOS_APLICACION['movil']:
                enviar_mensaje_cola(COLA_MONKEY_MOVIL, herramienta, resultado)
