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
COLA_CALABASH = SQS.get_queue_by_name(QueueName=settings.SQS_CALABASH_NAME)

if __name__ == '__main__':
    while True:
        print('Entra ciclo')
        for message in COLA_CALABASH.receive_messages(MaxNumberOfMessages=1, MessageAttributeNames=['Id']):
            if message.message_attributes is not None:
                resultado_id = message.message_attributes.get('Id').get('StringValue')
                resultado = Resultado.objects.get(id=int(resultado_id))
                # Copiar el script de la prueba a donde lo necesita calabash para poder ejecutarlo
                ruta_archivo = util.copiar_contenido(
                    resultado, settings.CALABASH_PATH, settings.RUTAS_INTERNAS["Calabash"], '.feature')
                # Se firma el .apk
                salida_firmado = subprocess.run(['calabash-android', 'resign', resultado.solicitud.version.apk.path],
                                                shell=True, check=False, cwd=settings.CALABASH_PATH,
                                                stdout=subprocess.PIPE)
                # levantar el emulador y esperar hasta que este listo
                util.iniciar_emulador(resultado.solicitud.dispositivo.nombre_tecnico)
                # Ejecutar el comando de calabash
                salida_ejecucion = subprocess.run(['calabash-android', 'run', resultado.solicitud.version.apk.path,
                                                   ruta_archivo], check=False, shell=True, cwd=settings.CALABASH_PATH,
                                                  stdout=subprocess.PIPE)
                # print('La salida firmado:', salida_firmado.stdout.decode('utf-8'))
                # print('La salida ejecucion:', salida_ejecucion.stdout.decode('utf-8'))
                resultado.exitoso = salida_ejecucion.returncode == 0
                util.eliminar_emulador()
                archivo_log = open(str(resultado.id) + "log.txt", "w+")
                archivo_log.write(salida_ejecucion.stdout.decode('utf-8'))

                resultado.log.save('log_calabash.txt', archivo_log, save=True)
                resultado.terminada = True
                resultado.save()
                archivo_log.close()
                os.remove(archivo_log.name)
                util.recoger_screenshoots(resultado)
                message.delete()
                util.validar_ultimo(resultado.solicitud)
        time.sleep(settings.TIEMPO_ESPERA_WORKERS)
