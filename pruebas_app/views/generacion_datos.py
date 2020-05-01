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
from pruebas_app.views import guardar_prueba
from pruebas_automaticas import settings

def configurar_cucumber(request, estrategia_id):
    estrategia = Estrategia.objects.get(id=estrategia_id)
    return render(request, 'pruebas_app/configurar_cucumber.html',
                  {'estrategia': estrategia})

def guardar_configuracion_cucumber(request, estrategia_id):
    print(request)
    guardar_prueba(request, estrategia_id);
    return HttpResponseRedirect(reverse('agregar_prueba', args=[estrategia_id]))