import json
import os
import shutil
from decimal import Decimal
from zipfile import ZipFile
from django.core.files import File
import django
import glob
import subprocess
from django.conf import settings
from django.core.files.base import ContentFile

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
    if informacion > sensibilidad_VRT:
        fallida = True
    else:
        fallida = False
    return fallida


# Este metodo se ejecuta cuando una solicitud tiene VRT y lo que hace es recorrer todos los resultados de ambas
# solicitudes y todos sus screenshoots y a cada screensoot reciproco le ejecuta VRT
def ejecutar_vrt(solicitud_posterior):
    # Se sacan los resultados de ambas solicitudes
    resultados_posteriores = solicitud_posterior.resultado_set.all()
    print('posteriores:', resultados_posteriores)
    resultados_anteriores = solicitud_posterior.solicitud_VRT.resultado_set.all()
    print('anteriores:', resultados_anteriores)

    # Se recorren los resultados
    for i in range(resultados_anteriores.count()):
        # de cada resultado de cada solicitud se sacan los screenshots
        screenshots_posteriores = resultados_posteriores[i].screenshot_set.all()
        print('screen posteriores:', screenshots_posteriores)
        screenshots_anteriores = resultados_anteriores[i].screenshot_set.all()
        print('screen anteriores:', screenshots_anteriores)

        # Se recorre cada screenshot de cada resultado y esos son los que se comparan
        for j in range(screenshots_anteriores.count()):
            # las imagenes para comparar no es necesario subirlas nuevamente, solo se referencian las originales
            imagen_posterior = screenshots_posteriores[j].imagen
            imagen_anterior = screenshots_anteriores[j].imagen

            # para la imagen diferencias se crea una ruta ficticia en la cual resemble creara la nueva imagen
            imagen_diferencias = settings.BASE_DIR + '//archivos//screenshots//VRT//' + str(
                solicitud_posterior.id) + 'diferencia.png '

            comando = subprocess.run(
                ['node', 'index.js', imagen_anterior.path, imagen_posterior.path,
                 imagen_diferencias], shell=True, cwd=settings.RESEMBLE_PATH, stdout=subprocess.PIPE)

            # Se guarda en informacion el json generado por resemble
            informacion = comando.stdout.decode('utf-8')
            print("la salida es:", informacion)

            # Se valida resultado de vrt
            json_content = json.dumps(informacion)
            diferencia_real = json_content.split("'")[1].split("'")[-1]
            validacion = validar_resultado_vrt(Decimal(diferencia_real), solicitud_posterior.sensibilidad_VRT)

            # Solo se guarda la imagen cuando se encuentran diferencias
            if validacion:
                resultado_vrt = ResultadoVRT()
                resultado_vrt.screenshoot_previo = imagen_anterior
                resultado_vrt.screenshoot_posterior = imagen_posterior
                resultado_vrt.informacion = informacion
                resultado_vrt.solicitud = solicitud_posterior
                resultado_vrt.fallida = validacion

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


if __name__ == '__main__':
    mutacion = Mutacion.objects.get(id=6)
    recoger_mutantes(mutacion)
