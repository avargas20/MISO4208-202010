import os
import subprocess

import django
from django.core.files import File

from pruebas_automaticas import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_app.settings")
django.setup()
from common import util

from pruebas_app.models import Resultado


def funcion(resultado_id):
    
    nuevo_archivo = util.copiar_contenido(resultado_id, settings.RUTAS_INTERNAS["Cypress"])
    resultado = Resultado.objects.get(id=resultado_id)
    
    salida = subprocess.call(['npx', 'cypress', 'run', 'cypress:run', '--spec', nuevo_archivo], shell=True, cwd=settings.CYPRESS_PATH)

    print('La salida es:',salida)
    
    video = open(settings.CYPRESS_PATH+'//cypress//videos//'+str(resultado.id)+'.js.mp4', 'rb')
    archivo_video = File(video)
    resultado.resultado.save('cypress.mp4', archivo_video, save=True)
    resultado.terminada = True
    resultado.save()
    video.close()
    util.validar_ultimo(resultado.solicitud)
