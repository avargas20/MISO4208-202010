from pruebas_app.models import Aplicacion, Prueba, Version, Herramienta, Tipo, Estrategia, Solicitud, Resultado
from pruebas_automaticas import settings
import os
import django
import subprocess
from django.core.files import File
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_app.settings")
django.setup()

# Este metodo se encarga de copiar el codigo del script de la prueba en la ruta donde la herramienta necesite ese script para poder correr la prueba
def copiar_contenido(resultado_id, ruta_interna):
    print("En el resultado:", resultado_id)
    resultado = Resultado.objects.get(id=resultado_id)
    prueba = resultado.prueba
    print("El script es:",prueba.script)

    f=open(prueba.script.path, "r")
    contenido = f.read()
    print("El contenido es:",contenido)
    nuevo_archivo = ruta_interna+str(resultado.id)+".js"
    ruta_nuevo_ejecutable = os.path.join(settings.CYPRESS_PATH, nuevo_archivo)
    with open(ruta_nuevo_ejecutable, "w+") as file:
        file.write(contenido)
    return nuevo_archivo
