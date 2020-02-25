from django.shortcuts import render

from .serializer import EstrategiaSerializer
from .models import Aplicacion, Prueba, Version, Herramienta, Tipo, Estrategia, Solicitud, Resultado
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
import json
import scripts.worker_cypress


# Create your views here.

def home(request):
    solicitudes = Solicitud.objects.all().order_by('-id')
    return render(request, 'pruebas_app/index.html')


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
    return render(request, 'pruebas_app/agregar_prueba.html',
                  {'aplicacion': estrategia.version.aplicacion, 'version': estrategia.version, 'estrategia': estrategia,
                   'herramientas': herramientas, 'tipos': tipos, 'pruebas': pruebas})


def guardar_prueba(request, estrategia_id):
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


def obtener_versiones_de_una_aplicacion(request):
    aplicacion_id = int(request.GET['aplicacion_id'])
    print("ajax aplicacion_id ", aplicacion_id)

    result_set = []
    versiones = []
    aplicacion = Aplicacion.objects.get(id=aplicacion_id)
    print("selected app name ", aplicacion)
    versiones = Version.objects.filter(aplicacion=aplicacion)
    for v in versiones:
        print("version number", v.numero)
        result_set.append({'numero': v.numero, 'id': v.id})
    return HttpResponse(json.dumps(result_set), content_type='application/json')


def lanzar_estrategia(request):
    estrategias = Estrategia.objects.all()
    return render(request, 'pruebas_app/lanzar_estrategia.html', {'estrategias': estrategias})


def ver_estrategia(request, estrategia_id):
    estrategias = Estrategia.objects.all()
    return render(request, 'pruebas_app/lanzar_estrategia.html', {'estrategias': estrategias})


def ejecutar_estrategia(request, estrategia_id):
    estrategia = Estrategia.objects.get(id=estrategia_id)
    solicitud = Solicitud()
    solicitud.estrategia = estrategia
    solicitud.save()

    for p in estrategia.prueba_set.all():
        herramienta = p.herramienta.nombre
        resultado = Resultado()
        resultado.solicitud = solicitud
        resultado.prueba = p
        resultado.save()
        # Aqui se debe mandar el mensaje a la cola respectiva (por ahora voy a lanzar el proceso manual)
        if herramienta == 'Cypress':
            scripts.worker_cypress.funcion(resultado.id)
            pass
        elif herramienta == 'Protractor':
            pass


def listar_estrategias(self):
    estrategia = Estrategia.objects.all()
    serializer = EstrategiaSerializer(estrategia, many=True)
    return JsonResponse(serializer.data, safe=False)
