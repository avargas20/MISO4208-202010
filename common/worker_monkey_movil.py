import os
import subprocess
import time

import boto3
import django

from common import util
from pruebas_app.models import Resultado
from pruebas_automaticas import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_app.settings")
django.setup()

SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_MONKEY_MOVIL = SQS.get_queue_by_name(QueueName=settings.SQS_MONKEY_MOVIL_NAME)

if __name__ == '__main__':
    while True:
        print('Entra ciclo')
        for message in COLA_MONKEY_MOVIL.receive_messages(MaxNumberOfMessages=1, MessageAttributeNames=['Id']):
            if message.message_attributes is not None:
                nombre_paquete = ''
                ruta_apk = ''
                resultado_id = message.message_attributes.get('Id').get('StringValue')
                resultado = Resultado.objects.get(id=int(resultado_id))
                if resultado.solicitud.mutante:
                    nombre_paquete = resultado.solicitud.mutante.mutacion.version.nombre_paquete
                    ruta_apk = resultado.solicitud.mutante.apk_firmado.path
                else:
                    nombre_paquete = resultado.solicitud.version.nombre_paquete
                    ruta_apk = resultado.solicitud.version.apk.path
                numero_eventos = str(resultado.prueba.numero_eventos)
                semilla = resultado.prueba.semilla
                # iniciamos el emulador y esperamos a que este listo (el metodo lo hace)
                util.iniciar_emulador(resultado.solicitud.dispositivo.nombre_tecnico)
                # primero desinstalamos la aplicación y luego la volvemos a instalar para limpiar cualquier estado
                subprocess.call(['adb', 'uninstall', nombre_paquete], shell=True, cwd=os.path.join(
                    settings.ANDROID_SDK, settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']))
                subprocess.call(['adb', 'install', ruta_apk], shell=True, cwd=os.path.join(
                    settings.ANDROID_SDK, settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']))
                # Ahora ejecutar el monkey
                if semilla:
                    salida = subprocess.run(
                        ['adb', 'shell', 'monkey', '-p', nombre_paquete, '--pct-syskeys', '0', '-s', semilla, '-v',
                         numero_eventos],
                        shell=True,
                        check=False,
                        cwd=os.path.join(settings.ANDROID_SDK, settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']),
                        stdout=subprocess.PIPE)
                else:
                    salida = subprocess.run(
                        ['adb', 'shell', 'monkey', '-p', nombre_paquete, '--pct-syskeys', '0', '-v', numero_eventos],
                        shell=True,
                        check=False,
                        cwd=os.path.join(settings.ANDROID_SDK, settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']),
                        stdout=subprocess.PIPE)
                # matamos el emulador
                util.eliminar_emulador()
                # guardamos la salida del comando
                log_proceso = salida.stdout.decode('utf-8')
                # Determinamos si el monkey finalizo con exito
                resultado.exitoso = log_proceso[-17:].strip() == 'Monkey finished'
                archivo_log = open("log.txt", "w+")
                archivo_log.write(log_proceso)

                # print('La salida es:', salida.stdout.decode('utf-8'))

                resultado.log.save('log_monkey_android.txt', archivo_log, save=True)
                resultado.terminada = True
                resultado.save()
                archivo_log.close()
                os.remove(archivo_log.name)
                message.delete()
                util.validar_ultimo(resultado.solicitud)
        time.sleep(settings.TIEMPO_ESPERA_WORKERS)
