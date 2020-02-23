from pruebas_automaticas import settings
import os
import django
import subprocess
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_app.settings")
django.setup()

from pruebas_app.models import Aplicacion, Prueba, Version, Herramienta, Tipo, Estrategia, Solicitud, Resultado


def funcion(resultado_id):

    print(resultado_id)
    resultado = Resultado.objects.get(id=resultado_id)
    prueba = resultado.prueba
    print(prueba.script)

    

    salida = subprocess.call(['npx', 'cypress', 'run'], shell=True, cwd=settings.CYPRESS_PATH)