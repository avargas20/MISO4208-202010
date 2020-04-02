import boto3
import os
import subprocess
import django
import time
from common import util
from pruebas_automaticas import settings
from pruebas_app.models import Resultado

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_app.settings")
django.setup()

SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_MONKEY_MOVIL = SQS.get_queue_by_name(QueueName=settings.SQS_MONKEY_MOVIL_NAME)

if __name__ == '__main__':
    while True:
        print('Entra ciclo')
        for message in COLA_MONKEY_MOVIL.receive_messages(MaxNumberOfMessages=1, MessageAttributeNames=['Id']):
            if message.message_attributes is not None:
                resultado_id = message.message_attributes.get('Id').get('StringValue')
                resultado = Resultado.objects.get(id=int(resultado_id))
                nombre_paquete = resultado.solicitud.version.nombre_paquete
                numero_eventos = str(resultado.prueba.numero_eventos)
                # levantamos el emulador
                subprocess.Popen(['emulator', resultado.solicitud.dispositivo.nombre_tecnico], shell=True,
                                 cwd=os.path.join(settings.ANDROID_SDK, 'emulator'))
                # primero desinstalamos la aplicación y luego la volvemos a instalar para limpiar cualquier estado
                subprocess.call(['adb', 'uninstall', nombre_paquete], shell=True, cwd=os.path.join(
                    settings.ANDROID_SDK, settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']))
                subprocess.call(['adb', 'install', resultado.solicitud.version.apk.path], shell=True, cwd=os.path.join(
                    settings.ANDROID_SDK, settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']))
                # Ahora ejecutar el monkey

                salida = subprocess.run(
                    ['adb', 'shell', 'monkey', '-p', nombre_paquete, '--pct-syskeys', '0', '-v', numero_eventos], shell=True,
                    check=False,
                    cwd=os.path.join(settings.ANDROID_SDK, settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']),
                    stdout=subprocess.PIPE)
                # matamos el emulador
                subprocess.call("adb -s emulator-5554 emu kill".split(), shell=True,
                                cwd=os.path.join(settings.ANDROID_SDK,
                                                 settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']))
                archivo_log = open("log.txt", "w+")
                archivo_log.write(salida.stdout.decode('utf-8'))

                # print('La salida es:', salida.stdout.decode('utf-8'))

                resultado.log.save('log.txt', archivo_log, save=True)
                resultado.terminada = True
                resultado.save()
                archivo_log.close()
                os.remove(archivo_log.name)
                message.delete()
                util.validar_ultimo(resultado.solicitud)
        time.sleep(settings.TIEMPO_ESPERA_WORKERS)
