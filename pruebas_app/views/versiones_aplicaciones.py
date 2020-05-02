import json
import os
import subprocess

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from pruebas_app.models import Aplicacion, Version, TipoAplicacion
from pruebas_automaticas import settings


def nueva_aplicacion(request):
    aplicaciones = Aplicacion.objects.all()
    tipos = TipoAplicacion.objects.all()
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


def eliminar_version(version_id):
    version = Version.objects.get(id=version_id)
    version.delete()
    return HttpResponseRedirect(reverse('nueva_aplicacion'))


def obtener_versiones_de_una_aplicacion(request):
    aplicacion_id = int(request.GET['aplicacion_id'])
    result_set = []
    aplicacion = Aplicacion.objects.get(id=aplicacion_id)
    versiones = Version.objects.filter(aplicacion=aplicacion)
    for version in versiones:
        result_set.append({'numero': version.numero, 'id': version.id})
    return HttpResponse(json.dumps(result_set), content_type='application/json')
