import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_app.settings")

from pruebas_app.models import Aplicacion, Prueba, Version, Herramienta, Tipo, Estrategia, Solicitud, Resultado
from pruebas_automaticas import settings
from django.core.files import File
import subprocess
from zipfile import ZipFile
import django
django.setup()



def main():
    solicitud = Solicitud.objects.filter(id=90)
    validar_ultimo(solicitud)


if __name__ == '__main__':
    main()

# Este metodo se encarga de copiar el codigo del script de la prueba en la ruta donde la herramienta necesite ese script para poder correr la prueba


def copiar_contenido(resultado_id, ruta_interna):
    print("En el resultado:", resultado_id)
    resultado = Resultado.objects.get(id=resultado_id)
    prueba = resultado.prueba
    print("El script es:", prueba.script)

    f = open(prueba.script.path, "r")
    contenido = f.read()
    print("El contenido es:", contenido)
    nuevo_archivo = ruta_interna+str(resultado.id)+".js"
    ruta_nuevo_ejecutable = os.path.join(settings.CYPRESS_PATH, nuevo_archivo)
    with open(ruta_nuevo_ejecutable, "w+") as file:
        file.write(contenido)
    return nuevo_archivo


def validar_ultimo(solicitud):
    if(solicitud.terminada):
        zip_objetcs = ZipFile('evidencias.zip', 'w')
        for r in solicitud.resultado_set.all():
            zip_objetcs.write(r.resultado.path)
        solicitud.evidencia.save('evidencias.zip', zip_objetcs, save=True)
        zip_objetcs.close()
