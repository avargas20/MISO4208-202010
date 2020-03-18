import os

import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_automaticas.settings")
django.setup()

from pruebas_app.models import Solicitud, Resultado

from pruebas_automaticas import settings
from django.core.files import File
from zipfile import ZipFile


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
            if bool(r.resultado):
                zip_objetcs.write(r.resultado.path, r.resultado.name)
            if bool(r.log):
                zip_objetcs.write(r.log.path, r.log.name)
        zip_objetcs.close()
        archivo = open(settings.BASE_DIR+"//evidencias.zip", 'rb')    
        archivo_zip = File(archivo)
        solicitud.evidencia.save('evidencias.zip', archivo_zip, save=True)
        archivo_zip.close()
        os.remove(settings.BASE_DIR+"//evidencias.zip")

def main():
    solicitud = Solicitud.objects.filter(id=90)
    validar_ultimo(solicitud)


if __name__ == '__main__':
    main()