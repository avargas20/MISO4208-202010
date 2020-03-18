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
    
    resultado = Resultado.objects.get(id=resultado_id)
    nombre_paquete = resultado.prueba.estrategia.version.nombre_paquete
    #primero desinstalamos la aplicacion y luego la volvemos a instalar para limpiar cualquier estado
    subprocess.call(['adb', 'uninstall', nombre_paquete], shell=True, cwd=os.path.join(settings.ANDROID_SDK, settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']))
    subprocess.call(['adb', 'install', resultado.prueba.estrategia.version.apk.path], shell=True, cwd=os.path.join(settings.ANDROID_SDK, settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']))
    #Ahora ejecutar el monkey

    salida = subprocess.run(['adb', 'shell', 'monkey', '-p', nombre_paquete, '--pct-syskeys', '0', '-v', '10'], shell=True, cwd=os.path.join(settings.ANDROID_SDK, settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']), stdout=subprocess.PIPE)

    archivo_log= open("log.txt","w+")
    archivo_log.write(salida.stdout.decode('utf-8'))

    #print('La salida es:', salida.stdout.decode('utf-8'))
    

    resultado.log.save('log.txt', archivo_log, save=True)
    resultado.terminada = True
    resultado.save()
    archivo_log.close()
    os.remove(archivo_log.name)
    util.validar_ultimo(resultado.solicitud)