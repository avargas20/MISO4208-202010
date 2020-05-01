from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from pruebas_app.models import Estrategia
from pruebas_app.views import guardar_prueba


def configurar_cucumber(request, estrategia_id):
    estrategia = Estrategia.objects.get(id=estrategia_id)
    return render(request, 'pruebas_app/configurar_cucumber.html',
                  {'estrategia': estrategia})


def guardar_configuracion_cucumber(request, estrategia_id):
    print(request)
    guardar_prueba(request, estrategia_id)
    return HttpResponseRedirect(reverse('agregar_prueba', args=[estrategia_id]))
