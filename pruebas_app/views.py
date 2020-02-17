from django.shortcuts import render
from .models import Aplicacion, Version, Herramienta, Tipo, Estrategia
from django.http import HttpResponse
import json

# Create your views here.

def home(request):
    return render(request, 'pruebas_app/index.html')

def agregar_estrategia(request):
    aplicaciones = Aplicacion.objects.all()
    versiones = Version.objects.all() #Hay que sacar la versiones de la app seleccionada, ver notas
    herramientas = Herramienta.objects.all()
    tipos = Tipo.objects.all()
    return render(request, 'pruebas_app/agregar_estrategia.html', {'aplicaciones': aplicaciones, 'versiones': versiones, 'herramientas': herramientas, 'tipos': tipos})

def obtener_versiones_de_una_estrategia(request):
    aplicacion_id = int(request.GET['aplicacion_id'])
    print ("ajax aplicacion_id ", aplicacion_id)

    result_set = []
    versiones = []
    aplicacion = Aplicacion.objects.get(id=aplicacion_id)
    print ("selected app name ", aplicacion)
    versiones = Version.objects.filter(aplicacion=aplicacion)
    for v in versiones:
        print ("version name", v.numero)
        result_set.append({'numero': v.numero})
    return HttpResponse(json.dumps(result_set), content_type='application/json')


def lanzar_estrategia(request):
    estrategias = Estrategia.objects.all()
    return render(request, 'pruebas_app/lanzar_estrategia.html', {'estrategias': estrategias} )