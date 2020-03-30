import os
import subprocess
import boto3
import django
from django.core.files import File
from common import util
from pruebas_automaticas import settings
from pruebas_app.models import Resultado

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_app.settings")
django.setup()

SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_PUPPETEER = SQS.get_queue_by_name(QueueName=settings.SQS_PUPPETEER_NAME)

if __name__ == '__main__':
    print('entra')
    while True:
        for message in COLA_PUPPETEER.receive_messages(MaxNumberOfMessages=1, MessageAttributeNames=['Id']):
            if message.message_attributes is not None:
                resultado_id = message.message_attributes.get('Id').get('StringValue')
                resultado = Resultado.objects.get(id=int(resultado_id))

                nuevo_archivo = util.copiar_contenido(resultado, settings.PUPPETEER_PATH,
                                                      settings.RUTAS_INTERNAS["Puppeteer"], '.test.js')

                salida = subprocess.run(['jest', nuevo_archivo], shell=True, check=False, cwd=settings.PUPPETEER_PATH,
                                        stdout=subprocess.PIPE)

                print('Salida:', salida.stdout.decode('utf-8'))

                archivo_log = open(str(resultado.id) + "log.txt", "w+")
                archivo_log.write(salida.stdout.decode('utf-8'))

                resultado.log.save('log_puppeteer.txt', archivo_log, save=True)
                resultado.terminada = True
                resultado.save()
                archivo_log.close()
                os.remove(archivo_log.name)
                message.delete()
                util.validar_ultimo(resultado.solicitud)
