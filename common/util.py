import glob
import json
import os
import shutil
import subprocess
from decimal import Decimal
from zipfile import ZipFile

import django
from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from faker import Faker

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_automaticas.settings")
django.setup()

from pruebas_app.models import ScreenShot, ResultadoVRT, Mutante, Mutacion, Operador


# Este metodo se encarga de copiar el codigo del script de la prueba en la ruta donde la herramienta necesite ese
# script para poder correr la prueba
def copiar_contenido(resultado, ruta_herramienta, ruta_interna, extension_archivo):
    print("En el resultado:", resultado)
    prueba = resultado.prueba
    print("El script inicial es:", prueba.script)
    archivo = open(prueba.script.path, "r")
    contenido = archivo.read()
    print("El contenido inicial es:", contenido)
    print('Heeramienta', prueba.herramienta.nombre)
    print(prueba.herramienta.nombre != "Calabash")
    if prueba.herramienta.nombre != "Calabash":
        contenido = contenido.replace("-urlToken-", resultado.solicitud.version.url)
        print("El nuevo contenido es:", contenido)
        if resultado.prueba.tipo.nombre == settings.TIPOS_PRUEBAS["aleatorias"]:
            contenido = contenido.replace("-randomToken-", str(prueba.numero_eventos))
            print("El nuevo contenido con random es:", contenido)

    nuevo_archivo = ruta_interna + str(resultado.id) + extension_archivo
    ruta_nuevo_ejecutable = os.path.join(ruta_herramienta, nuevo_archivo)

    with open(ruta_nuevo_ejecutable, "w+") as file:
        file.write(contenido)
    return nuevo_archivo


# Este metodo valida que si la solicitud esta terminada, debe agrupar todos los resultados en un solo .zip y
# guardarlos como evidencias, todos los workers lo deben llamar
def validar_ultimo(solicitud):
    if solicitud.terminada:
        zip_objetcs = ZipFile(settings.BASE_DIR + '//evidencias.zip', 'w')

        if bool(solicitud.solicitud_VRT):
            ejecutar_vrt(solicitud)

        for a in solicitud.resultadovrt_set.all():
            if bool(a.imagen_diferencias):
                zip_objetcs.write(a.imagen_diferencias.path, a.imagen_diferencias.name)

        for r in solicitud.resultado_set.all():
            if bool(r.resultado):
                zip_objetcs.write(r.resultado.path, r.resultado.name)
            if bool(r.log):
                zip_objetcs.write(r.log.path, r.log.name)
            for s in r.screenshot_set.all():
                if bool(s.imagen):
                    zip_objetcs.write(s.imagen.path, s.imagen.name)

        zip_objetcs.close()
        archivo = open(settings.BASE_DIR + "//evidencias.zip", 'rb')
        archivo_zip = File(archivo)
        solicitud.evidencia.save('evidencias.zip', archivo_zip, save=True)
        archivo_zip.close()
        os.remove(settings.BASE_DIR + "//evidencias.zip")


# Este metodo valida si la prueba de VRT reporta cambios segun el % proporcionado al momento de la ejecucion
def validar_resultado_vrt(informacion, sensibilidad_VRT):
    return True if informacion >= sensibilidad_VRT else False


# Este metodo consolida todos los screenshots de todas las pruebas
def screenshots_vrt(solicitud_posterior):
    # Se sacan los resultados de ambas solicitudes
    resultados_posteriores = solicitud_posterior.resultado_set.all()
    print('posteriores:', resultados_posteriores)
    resultados_anteriores = solicitud_posterior.solicitud_VRT.resultado_set.all()
    print('anteriores:', resultados_anteriores)
    # Se sacan los screenshots de cada prueba
    consolidado_posteriores = []
    consolidado_anteriores = []

    for k in resultados_posteriores:
        for x in k.screenshot_set.all():
            consolidado_posteriores.append(x)
    print('todos posteriores:', consolidado_posteriores, '--lenght----', len(consolidado_posteriores))

    for l in resultados_anteriores:
        for x in l.screenshot_set.all():
            consolidado_anteriores.append(x)
    print('todos anteriores:', consolidado_anteriores, '--lenght----', len(consolidado_anteriores))
    return consolidado_anteriores, consolidado_posteriores


# Este metodo se ejecuta cuando una solicitud tiene VRT y lo que hace es recorrer todos los resultados de ambas
# solicitudes y todos sus screenshoots y a cada screensoot reciproco le ejecuta VRT
def ejecutar_vrt(solicitud_posterior):
    consolidado_anteriores, consolidado_posteriores = screenshots_vrt(solicitud_posterior)
    # se comparan imagenes
    for i in consolidado_posteriores:
        for j in consolidado_anteriores:
            if i.nombre == j.nombre:
                print("imagenes a comparar------------posterior: --->", i.nombre, "anterior: ----->", j.nombre)
                # para la imagen diferencias se crea una ruta ficticia en la cual resemble creara la nueva imagen
                imagen_diferencias = settings.BASE_DIR + '//archivos//screenshots//VRT//' + str(
                    solicitud_posterior.id) + 'diferencia.png'

                comando = subprocess.run(
                    ['node', 'index.js', j.imagen.path, i.imagen.path,
                     imagen_diferencias], shell=True, cwd=settings.RESEMBLE_PATH, stdout=subprocess.PIPE)
                print('returnCodeVRT:', comando.returncode)
                # Se guarda en informacion el json generado por resemble
                informacion = comando.stdout.decode('utf-8')
                print("la salida es:", informacion)

                # Se valida resultado de vrt
                json_content = json.dumps(informacion)
                diferencia_real = json_content.split("'")[1].split("'")[-1]
                validacion = validar_resultado_vrt(Decimal(diferencia_real), solicitud_posterior.sensibilidad_VRT)
                print('validacion', validacion)
                # Solo se guarda la imagen cuando se encuentran diferencias
                if validacion:
                    resultado_vrt = ResultadoVRT()
                    resultado_vrt.screenshoot_previo = j.imagen
                    resultado_vrt.screenshoot_posterior = i.imagen
                    resultado_vrt.informacion = informacion
                    resultado_vrt.solicitud = solicitud_posterior
                    resultado_vrt.fallida = validacion
                    resultado_vrt.porcentaje = diferencia_real
                    imagen_diff = open(imagen_diferencias, 'rb')
                    resultado_vrt.imagen_diferencias.save('diferencia.png', File(imagen_diff), save=True)
                    imagen_diff.close()
                    resultado_vrt.save()
                os.remove(imagen_diferencias)


# Este metodo busca recoger todos los screenshoots tomados por los scripts y guardarlos en la tabla ScreenShoot
def recoger_screenshoots(resultado):
    # La ruta depende de la herramienta que ejecuto la prueba
    ruta_a_recoger = determinar_ruta(resultado)
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
    elif nombre_herramienta == settings.TIPOS_HERRAMIENTAS["puppeteer"]:
        return settings.PUPPETEER_PATH
    elif nombre_herramienta == settings.TIPOS_HERRAMIENTAS["cucumber"]:
        return settings.CUCUMBER_PATH


# Este metodo inicia el emulador que tenga como nombre el parametro y espera a que este arranque
def iniciar_emulador(nombre_tecnico):
    # levantamos el emulador
    subprocess.Popen(['emulator', nombre_tecnico], shell=True, cwd=os.path.join(settings.ANDROID_SDK, 'emulator'))
    # esperamos hasta que este disponible
    subprocess.call(['adb', 'wait-for-device'], shell=True, cwd=settings.ANDROID_SDK)


# Este metodo consulta los emuladores encendidos y los detiene todos
def eliminar_emulador():
    # consultamos todos los emuladores prendidos
    comando_devices = subprocess.run(['adb', 'devices'], shell=True, check=False, cwd=settings.ANDROID_SDK,
                                     stdout=subprocess.PIPE)
    salida = comando_devices.stdout.decode('utf-8')
    print('devices a eliminar: ', salida)
    # partir por saltos de lineas (splitlines()) y coger desde la segunda hasta la penultima ([1:-1])
    # y luego partir por \t y validar si la segunda posicion indica que el dispositivo esta prendido (== 'device')
    # en caso de estarlo tomar la primer posicion que indica el nombre del dispositivo
    devices = [linea.split('\t')[0] for linea in salida.splitlines()[1:-1] if linea.split('\t')[1] == 'device']
    print('lineas a eliminar', devices)
    for d in devices:
        subprocess.call(d.join(['adb -s ', ' emu kill']).split(), shell=True,
                        cwd=os.path.join(settings.ANDROID_SDK, settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']))


def configurar_archivo_operadores(mutacion):
    with open(os.path.join(settings.MUTAPK_PATH, 'properties', 'operators.properties'), "w+") as file:
        for o in mutacion.operadores.all():
            print(o)
            # Escribir en el archivo con el formato necesario numero tab igual tab nombre
            file.write('{0}\t=\t{1}\n'.format(o.numero, o.nombre))


# este metodo busca recoger los reportes que genera muteAPK con la informacion de los mutantes a generar
def recoger_reportes_mutacion(mutacion):
    # Creo una expersion que entregue los archivos JSON en la ruta de MuteAPK, mutants y solo debe haber 1
    reporte_json = glob.glob(os.path.join(settings.MUTAPK_PATH, 'mutants', '*.json'))[0]
    with open(reporte_json, 'r') as file_json:
        with ContentFile(file_json.read()) as file_json_content:
            # Saco el nombre y la extension del archivo para guardarlo asi mismo
            mutacion.reporte_json.save(reporte_json.split("\\")[-1], file_json_content, save=True)

    reporte_log = glob.glob(os.path.join(settings.MUTAPK_PATH, 'mutants', '*.log'))[0]
    with open(reporte_log, 'r') as file_log:
        with ContentFile(file_log.read()) as file_log_content:
            mutacion.reporte_log.save(reporte_log.split("\\")[-1], file_log_content, save=True)

    reporte_csv = glob.glob(os.path.join(settings.MUTAPK_PATH, 'mutants', '*.csv'))[0]
    with open(reporte_csv, 'r') as file_csv:
        with ContentFile(file_csv.read()) as file_csv_content:
            mutacion.reporte_csv.save(reporte_csv.split("\\")[-1], file_csv_content, save=True)


def recoger_mutantes(mutacion):
    ruta_mutantes = os.path.join(settings.MUTAPK_PATH, settings.RUTAS_INTERNAS2.Mutacion.value)
    # se recorren todos los folders de la ruta de muteAPK/mutants
    for folder_mutante in os.listdir(ruta_mutantes):
        if os.path.isdir(os.path.join(ruta_mutantes, folder_mutante)):
            # el numero del mutante lo saque del ultimo digito de la carpeta
            numero_mutante = int(folder_mutante[-1])
            numero_operador = obtener_numero_operador(numero_mutante, mutacion)
            operador = Operador.objects.get(numero=numero_operador)
            mutante = Mutante(mutacion=mutacion, operador=operador)
            mutante.save()
            # obtener el manifest del mutante, no todos los mutantes lo generan
            if os.path.isfile(os.path.join(ruta_mutantes, folder_mutante, 'AndroidManifest.xml')):
                with open(os.path.join(ruta_mutantes, folder_mutante, 'AndroidManifest.xml')) as file_manifest:
                    with ContentFile(file_manifest.read()) as file_manifest_content:
                        mutante.manifest.save('AndroidManifest.xml', file_manifest_content, save=True)
            else:
                mutante.manifest = None
            # obtener el apk del mutante, este se genera con el mismo nombre del que tenga la version, este tiene la
            # forma apk/nombre.apk
            nombre_apk = mutacion.version.apk.name.split('/')[1]
            with open(os.path.join(ruta_mutantes, folder_mutante, nombre_apk), 'rb') as file_apk:
                with ContentFile(file_apk.read()) as file_apk_content:
                    mutante.apk.save(nombre_apk, file_apk_content, save=True)
            # obtener el apk firmado que tambien genera muteAPK con el mismo nombre del apk original mas el nombre
            # -aligned-debugSigned.apk para eso le quito la ultima parte con [:-4]
            nombre_apk_firmado = nombre_apk[:-4] + '-aligned-debugSigned.apk'
            with open(os.path.join(ruta_mutantes, folder_mutante, nombre_apk_firmado), 'rb') as file_apk_firmado:
                with ContentFile(file_apk_firmado.read()) as file_apk_firmado_content:
                    mutante.apk_firmado.save(nombre_apk_firmado, file_apk_firmado_content, save=True)


# metodo para obtener el numero del operador, lo hago buscando en las lineas del .csv en la posicion: numero del mutante
# el .csv genera dos lineas por cada mutante que se logro generar, esa linea tiene los datos separados por ; y el
# segundo tiene el numero del operador
def obtener_numero_operador(numero_mutante, mutacion):
    with open(mutacion.reporte_csv.path, 'r') as file:
        lineas = file.readlines()
        return lineas[numero_mutante].split(';')[1]


# recibe un folder y elimina de forma segura todos los archivos y las carpetas con las subcarpetas
def limpiar_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


# Guarda los archivos .steps
def guardar_steps(steps):
    archivo = steps.open('r')
    contenido = archivo.read()
    nuevo_archivo = settings.RUTAS_INTERNAS["CucumberSteps"] + archivo.__str__()
    ruta_nuevo_steps = os.path.join(settings.CUCUMBER_PATH, nuevo_archivo)
    with open(ruta_nuevo_steps, "wb") as file:
        file.write(contenido)


def generar_tabla(script, cantidad, valores):
    archivo = script[0].open('r')
    contenido = archivo.read()
    nuevo_archivo = settings.RUTAS_INTERNAS["GeneracionTemporal"] + archivo.__str__()
    ruta_nuevo_steps = os.path.join(settings.MEDIA_ROOT, nuevo_archivo)
    with open(ruta_nuevo_steps, "wb") as file:
        file.write(contenido)

    with open(ruta_nuevo_steps, "a") as file:
        file.write("\n\n")
        file.write("\t\t")
        file.write("Examples:")
        file.write("\n\n")
        file.write("\t\t")
    for llave in valores:
        with open(ruta_nuevo_steps, "a") as file:
            file.write("|")
            file.write(llave)
    with open(ruta_nuevo_steps, "a") as file:
        file.write("|")
    y = 0
    while y < int(cantidad):
        with open(ruta_nuevo_steps, "a") as file:
            file.write("\n")
            file.write("\t\t")
        for llave in valores:
            valor_generado = generar_aleatorio(valores.get(llave))
            with open(ruta_nuevo_steps, "a") as file:
                file.write("|")
                file.write(valor_generado)
        with open(ruta_nuevo_steps, "a") as file:
            file.write("|")
        y += 1

    return ruta_nuevo_steps


fake = Faker()


def generar_aleatorio(llave):
    print("La llave o tipo de dato es:", llave)
    if llave == 'TEXTO':
        return fake.pystr()
    if llave == 'EMAIL':
        return fake.ascii_company_email()


if __name__ == '__main__':
    mutacion = Mutacion.objects.get(id=6)
    recoger_mutantes(mutacion)
