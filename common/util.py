import os
from zipfile import ZipFile
from django.core.files import File
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_automaticas.settings")
django.setup()


# Este metodo se encarga de copiar el codigo del script de la prueba en la ruta donde la herramienta necesite ese script para poder correr la prueba
def copiar_contenido(resultado, ruta_herramienta, ruta_interna, extension_archivo):
    print("En el resultado:", resultado)
    prueba = resultado.prueba
    print("El script es:", prueba.script)

    archivo = open(prueba.script.path, "r")
    contenido = archivo.read()
    print("El contenido es:", contenido)
    nuevo_archivo = ruta_interna + str(resultado.id) + extension_archivo
    ruta_nuevo_ejecutable = os.path.join(ruta_herramienta, nuevo_archivo)
    with open(ruta_nuevo_ejecutable, "w+") as file:
        file.write(contenido)
    return nuevo_archivo


# Este metodo valida que si la solicitud esta terminada, debe agrupar todos los resultados en un solo .zip y guardarlos como evidencias, todos los workers lo deben llamar
def validar_ultimo(solicitud):
    if (solicitud.terminada):
        zip_objetcs = ZipFile('evidencias.zip', 'w')
        for r in solicitud.resultado_set.all():
            if bool(r.resultado):
                zip_objetcs.write(r.resultado.path, r.resultado.name)
            if bool(r.log):
                zip_objetcs.write(r.log.path, r.log.name)
        zip_objetcs.close()
        archivo = open(settings.BASE_DIR + "//evidencias.zip", 'rb')
        archivo_zip = File(archivo)
        solicitud.evidencia.save('evidencias.zip', archivo_zip, save=True)
        archivo_zip.close()
        os.remove(settings.BASE_DIR + "//evidencias.zip")


# Este metodo se encarga de copiar el codigo del script de la prueba en la ruta donde la herramienta necesite ese script para poder correr la prueba
# , reemplazando el token por la URL del archivo
def copiar_contenido_token(resultado, ruta_herramienta, ruta_interna, extension_archivo):
    print("En el resultado:", resultado)
    prueba = resultado.prueba
    prueba.script = "Monkey.js"
    print("El script es:", prueba.script)
    url = resultado.solicitud.estrategia.version.url

    archivo = open(prueba.script.path, "r")
    contenido = archivo.read()
    contenido = contenido.replace('-urlToken-', url)
    print("El contenido luego de reemplazar es:", contenido)
    nuevo_archivo = ruta_interna + str(resultado.id) + extension_archivo
    ruta_nuevo_ejecutable = os.path.join(ruta_herramienta, nuevo_archivo)
    with open(ruta_nuevo_ejecutable, "w+") as file:
        file.write(contenido)
    return nuevo_archivo
