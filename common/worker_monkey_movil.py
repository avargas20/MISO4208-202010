import boto3
import os
import subprocess
import django
from common import util
from pruebas_automaticas import settings
from pruebas_app.models import Resultado
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_app.settings")
django.setup()

SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_MONKEY_MOVIL = SQS.get_queue_by_name(QueueName=settings.SQS_MONKEY_MOVIL_NAME)

if __name__ == '__main__':
    print('entra')
    while True:
        for message in COLA_MONKEY_MOVIL.receive_messages(MaxNumberOfMessages=1, MessageAttributeNames=['Id']):
            if message.message_attributes is not None:

                resultado_id = message.message_attributes.get('Id').get('StringValue')
                resultado = Resultado.objects.get(id=int(resultado_id))
                nombre_paquete = resultado.prueba.estrategia.version.nombre_paquete
                # primero desinstalamos la aplicacion y luego la volvemos a instalar para limpiar cualquier estado
                subprocess.call(['adb', 'uninstall', nombre_paquete], shell=True, cwd=os.path.join(
                    settings.ANDROID_SDK, settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']))
                subprocess.call(['adb', 'install', resultado.prueba.estrategia.version.apk.path], shell=True, cwd=os.path.join(
                    settings.ANDROID_SDK, settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']))
                # Ahora ejecutar el monkey

                salida = subprocess.run(['adb', 'shell', 'monkey', '-p', nombre_paquete, '--pct-syskeys', '0', '-v', '10'], shell=True, check=False,
                                        cwd=os.path.join(settings.ANDROID_SDK, settings.RUTAS_INTERNAS_SDK_ANDROID['platform-tools']), stdout=subprocess.PIPE)

                archivo_log = open("log.txt", "w+")
                archivo_log.write(salida.stdout.decode('utf-8'))

                #print('La salida es:', salida.stdout.decode('utf-8'))

                resultado.log.save('log.txt', archivo_log, save=True)
                resultado.terminada = True
                resultado.save()
                archivo_log.close()
                os.remove(archivo_log.name)
                message.delete()
                util.validar_ultimo(resultado.solicitud)
