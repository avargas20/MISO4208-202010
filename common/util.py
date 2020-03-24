import os
from zipfile import ZipFile
from django.core.files import File
import django
import glob
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_automaticas.settings")
django.setup()

from pruebas_app.models import ScreenShot

# Este metodo se encarga de copiar el codigo del script de la prueba en la ruta donde la herramienta necesite ese script para poder correr la prueba
def copiar_contenido(resultado, ruta_herramienta, ruta_interna, extension_archivo):
    print("En el resultado:", resultado)
    prueba = resultado.prueba
    print("El script es:", prueba.script)

    archivo = open(prueba.script.path, "r")
    contenido = archivo.read()
    print("El contenido es:", contenido)
    nuevo_archivo = ruta_interna+str(resultado.id)+extension_archivo
    ruta_nuevo_ejecutable = os.path.join(ruta_herramienta, nuevo_archivo)
    with open(ruta_nuevo_ejecutable, "w+") as file:
        file.write(contenido)
    return nuevo_archivo


# Este metodo valida que si la solicitud esta terminada, debe agrupar todos los resultados en un solo .zip y guardarlos como evidencias, todos los workers lo deben llamar
def validar_ultimo(solicitud):
    if(solicitud.terminada):
        zip_objetcs = ZipFile(settings.BASE_DIR+'//evidencias.zip', 'w')
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


# Este metodo busca recoger todos los screenshoots tomados por los scripts y guardarlos en la tabla ScreenShoot
def recoger_screenshoots(resultado):
    #La ruta depende de la herramienta que ejecuto la prueba
    ruta_a_recoger = determinar_ruta(resultado)
    #Se crea una expresion con *.png para que recoja esos tipos de archivos
    ruta_con_filtro = os.path.join(ruta_a_recoger, '*.png')
    imagenes = glob.glob(ruta_con_filtro)
    for imagen in imagenes:
        print('screens:', imagen)
        #Se saca el nombre del archivo sin extension
        nombre = imagen.split('\\')[-1].split('.')[0]
        screenshoot = ScreenShot()
        screenshoot.resultado = resultado
        #Se guarda para generar el id y que quede guardado el screenshoot con ese id
        screenshoot.save()
        file = open(imagen, 'rb')
        archivo = File(file)
        screenshoot.imagen.save(nombre, archivo, save=True)
        screenshoot.nombre = nombre
        screenshoot.save()
        archivo.close()
        #se borra al final cada screenshoot tomado porque ya existe en la ruta del proyecto
        os.remove(imagen)


def determinar_ruta(resultado):
    nombre_herramienta = resultado.prueba.herramienta.nombre
    if nombre_herramienta == settings.TIPOS_HERRAMIENTAS["cypress"]:
        return settings.CYPRESS_PATH
    elif nombre_herramienta == settings.TIPOS_HERRAMIENTAS["calabash"]:
        return settings.CALABASH_PATH
