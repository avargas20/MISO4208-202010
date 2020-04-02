import json
import os
from decimal import Decimal
from zipfile import ZipFile
from django.core.files import File
import django
import glob
import subprocess
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_automaticas.settings")
django.setup()

from pruebas_app.models import ScreenShot, ResultadoVRT


# Este metodo se encarga de copiar el codigo del script de la prueba en la ruta donde la herramienta necesite ese script para poder correr la prueba
def copiar_contenido(resultado, ruta_herramienta, ruta_interna, extension_archivo):
    print("En el resultado:", resultado)
    prueba = resultado.prueba
    print("El script inicial es:", prueba.script)
    archivo = open(prueba.script.path, "r")
    contenido = archivo.read()
    print("El contenido inicial es:", contenido)

    if prueba.herramienta is not "Calabash":
        contenido = contenido.replace("-urlToken-", resultado.solicitud.version.url)
        print("El nuevo contenido es:", contenido)

    nuevo_archivo = ruta_interna + str(resultado.id) + extension_archivo
    ruta_nuevo_ejecutable = os.path.join(ruta_herramienta, nuevo_archivo)

    with open(ruta_nuevo_ejecutable, "w+") as file:
        file.write(contenido)
    return nuevo_archivo


# Este metodo valida que si la solicitud esta terminada, debe agrupar todos los resultados en un solo .zip y guardarlos como evidencias, todos los workers lo deben llamar
def validar_ultimo(solicitud):
    if (solicitud.terminada):
        zip_objetcs = ZipFile(settings.BASE_DIR + '//evidencias.zip', 'w')
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
        if bool(solicitud.solicitud_VRT):
            ejecutar_vrt(solicitud)


# Este metodo se ejecuta cuando una solicitud tiene VRT y lo que hace es recorrer todos los resultados de ambas solicitudes y todos sus screenshoots y a cada screensoot reciproco
# le ejecuta VRT
def validar_resultado_vrt(informacion, sensibilidad_VRT, resultado_vrt):
    if informacion > sensibilidad_VRT:
        resultado_vrt.fallida = True
    else:
        resultado_vrt.fallida = False

    resultado_vrt.save()
    return r

def ejecutar_vrt(solicitud_posterior):
    # Se sacan los resultados de ambas solicitudes
    resultados_posteriores = solicitud_posterior.resultado_set.all()
    print('posteriores:', resultados_posteriores)
    resultados_anteriores = solicitud_posterior.solicitud_VRT.resultado_set.all()
    print('anteriores:', resultados_anteriores)

    # Se recorren los resultados, note que para que funcione deben tener la misma cantidad de resultados y haberse ejecutado en el mismo orden
    for i in range(resultados_anteriores.count()):
        # de cada resultado de cada solicitud se sacan los screenshots
        screenshots_posteriores = resultados_posteriores[i].screenshot_set.all()
        print('screen posteriores:', screenshots_posteriores)
        screenshots_anteriores = resultados_anteriores[i].screenshot_set.all()
        print('screen anteriores:', screenshots_anteriores)

        # Se recorre cada screenshot de cada resultado y esos son los que se comparan
        for j in range(screenshots_anteriores.count()):
            resultado_vrt = ResultadoVRT()
            resultado_vrt.solicitud = solicitud_posterior
            resultado_vrt.save()

            # las imagenes para comparar no es necesario subirlas nuevamente, solo se referencian las originales
            imagen_posterior = screenshots_posteriores[j].imagen
            imagen_anterior = screenshots_anteriores[j].imagen

            # para la imagen diferencias se crea una ruta ficticia en la cual resemble creara la nueva imagen
            imagen_diferencias = settings.BASE_DIR + '//archivos//screenshots//VRT//' + str(resultado_vrt.id) + '.png'
            resultado_vrt.screenshoot_posterior = imagen_posterior
            resultado_vrt.screenshoot_previo = imagen_anterior
            resultado_vrt.save()

            salida = subprocess.run(
                ['node', 'index.js', resultado_vrt.screenshoot_previo.path, resultado_vrt.screenshoot_posterior.path,
                 imagen_diferencias], shell=True, cwd=settings.RESEMBLE_PATH, stdout=subprocess.PIPE)

            resultado_vrt.informacion = salida.stdout.decode('utf-8')
            print("la salida es:", resultado_vrt.informacion)

            json_content = json.dumps(resultado_vrt.informacion)
            misMatchPercentage = json_content.split("'")[1].split("'")[-1]
            validar_resultado_vrt(Decimal(misMatchPercentage), solicitud_posterior.sensibilidad_VRT, resultado_vrt)

            # una vez resemble creo la imagen esta se guarda nuevamente pero en la solicitud_vrt y luego se borra la original
            print(imagen_diferencias)
            imagen_diff = open(imagen_diferencias, 'rb')
            resultado_vrt.imagen_diferencias.save('diferencia.png', File(imagen_diff), save=True)
            imagen_diff.close()
            os.remove(imagen_diferencias)
            resultado_vrt.save()


# Este metodo busca recoger todos los screenshoots tomados por los scripts y guardarlos en la tabla ScreenShoot
def recoger_screenshoots(resultado, ruta_a_recoger):
    # Se crea una expresion con *.png para que recoja esos tipos de archivos
    ruta_con_filtro = os.path.join(ruta_a_recoger, '*.png')
    imagenes = glob.glob(ruta_con_filtro)

    for imagen in imagenes:
        print('screens:', imagen)
        nombre = imagen.split("\\")[-1]
        screenshoot = ScreenShot()
        screenshoot.resultado = resultado
        # Se guarda para generar el id y que quede guardado el screenshoot con ese id
        screenshoot.save()
        file = open(imagen, 'rb')
        screenshoot.imagen.save(nombre, File(file), save=True)
        screenshoot.nombre = nombre
        screenshoot.save()
        file.close()
        # se borra al final cada screenshoot tomado de la ruta de la herramienta porque ya se guardo dentro del proyecto
        os.remove(imagen)


def determinar_ruta(resultado):
    nombre_herramienta = resultado.prueba.herramienta.nombre
    if nombre_herramienta == settings.TIPOS_HERRAMIENTAS["cypress"]:
        return settings.CYPRESS_PATH
    elif nombre_herramienta == settings.TIPOS_HERRAMIENTAS["calabash"]:
        return settings.CALABASH_PATH
