from django.shortcuts import render
from .models import Aplicacion, Version, Herramienta, Tipo, Estrategia

# Create your views here.

def home(request):
    return render(request, 'pruebas_app/index.html')

def agregar_estrategia(request):
    aplicaciones = Aplicacion.objects.all()
    versiones = Version.objects.all() #Hay que sacar la versiones de la app seleccionada, aqui hay un tuto https://simpleisbetterthancomplex.com/tutorial/2018/01/29/how-to-implement-dependent-or-chained-dropdown-list-with-django.html
    herramientas = Herramienta.objects.all()
    tipos = Tipo.objects.all()
    return render(request, 'pruebas_app/agregar_estrategia.html', {'aplicaciones': aplicaciones, 'versiones': versiones, 'herramientas': herramientas, 'tipos': tipos})

def lanzar_estrategia(request):
    estrategias = Estrategia.objects.all()
    return render(request, 'pruebas_app/lanzar_estrategia.html', {'estrategias': estrategias} )