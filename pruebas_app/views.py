from django.shortcuts import render
from .models import Aplicacion, Prueba, Version, Herramienta, Tipo, Estrategia
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
import json

# Create your views here.

def home(request):
    return render(request, 'pruebas_app/index.html')

def agregar_estrategia(request):
    aplicaciones = Aplicacion.objects.all()
    herramientas = Herramienta.objects.all()
    tipos = Tipo.objects.all()
    return render(request, 'pruebas_app/agregar_estrategia.html', {'aplicaciones': aplicaciones, 'herramientas': herramientas, 'tipos': tipos})

def guardar_estrategia(request):
    if request.method == 'POST':
        print(request.POST)
        version = Version.objects.get(id=request.POST['versiones'])
        nombre_estrategia = request.POST['nombre_estrategia']
        descripcion_estrategia = request.POST['descripcion_estrategia']
        estrategia = Estrategia(nombre=nombre_estrategia, descripcion=descripcion_estrategia, version=version)
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
    return render(request, 'pruebas_app/agregar_prueba.html', {'aplicacion': estrategia.version.aplicacion, 'version': estrategia.version, 'estrategia': estrategia, 'herramientas': herramientas, 'tipos': tipos, 'pruebas': pruebas})

def guardar_prueba( request, estrategia_id):
    if request.method == 'POST':
       
        _, script = request.FILES.popitem() 
        script = script[0]
        herramienta = Herramienta.objects.get(id=request.POST['herramienta'])
        tipo = Tipo.objects.get(id=request.POST['tipo'])
        estrategia = Estrategia.objects.get(id=estrategia_id)
        prueba = Prueba(script=script, herramienta=herramienta, tipo=tipo, estrategia=estrategia)
        prueba.save()

        print(request.POST)
        print(request.FILES)
        return agregar_prueba(request, estrategia_id)

def eliminar_prueba(request, prueba_id):
    prueba = Prueba.objects.get(id=prueba_id)
    estrategia_id = prueba.estrategia.id
    prueba.delete()
    return agregar_prueba(request, estrategia_id)


def obtener_versiones_de_una_estrategia(request):
    aplicacion_id = int(request.GET['aplicacion_id'])
    print ("ajax aplicacion_id ", aplicacion_id)

    result_set = []
    versiones = []
    aplicacion = Aplicacion.objects.get(id=aplicacion_id)
    print ("selected app name ", aplicacion)
    versiones = Version.objects.filter(aplicacion=aplicacion)
    for v in versiones:
        print ("version number", v.numero)
        result_set.append({'numero': v.numero, 'id': v.id})
    return HttpResponse(json.dumps(result_set), content_type='application/json')


def lanzar_estrategia(request):
    estrategias = Estrategia.objects.all()
    return render(request, 'pruebas_app/lanzar_estrategia.html', {'estrategias': estrategias} )