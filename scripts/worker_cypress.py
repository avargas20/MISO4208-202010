from pruebas_automaticas import settings
import os
import django
import subprocess
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_app.settings")
django.setup()

from pruebas_app.models import Aplicacion, Prueba, Version, Herramienta, Tipo, Estrategia, Solicitud, Resultado


def funcion(resultado_id):

    print("En el resultado:",resultado_id)
    resultado = Resultado.objects.get(id=resultado_id)
    prueba = resultado.prueba
    print("El script es:",prueba.script)

    f=open(prueba.script.path, "r")
    contenido = f.read()
    print("El contenido es:",contenido)
    nuevo_archivo = 'cypress/integration/'+str(resultado.id)+".js"
    ruta_nuevo_ejecutable = os.path.join(settings.CYPRESS_PATH, nuevo_archivo)
    with open(ruta_nuevo_ejecutable, "w+") as file:
        file.write(contenido)
    
    salida = subprocess.call(['npx', 'cypress', 'run', 'cypress:run', '--spec', nuevo_archivo], shell=True, cwd=settings.CYPRESS_PATH)

    print('La salida es:',salida)
    

