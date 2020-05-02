import zipfile
from io import BytesIO

import boto3
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.urls import reverse

from pruebas_app.models import Aplicacion, Version, Operador, Mutacion
from pruebas_automaticas import settings

SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_MUTACION = SQS.get_queue_by_name(QueueName=settings.SQS_MUTACION_NAME)


def crear_mutacion(request):
    aplicaciones = Aplicacion.objects.filter(tipo__tipo=settings.TIPOS_APLICACION2.Movil.value)
    operadores = Operador.objects.all()
    return render(request, 'pruebas_app/crear_mutacion.html', {'aplicaciones': aplicaciones, 'operadores': operadores})


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


def descargar_evidencias_mutacion(mutacion_id):
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
