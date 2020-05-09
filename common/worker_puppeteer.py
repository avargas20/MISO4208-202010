import os
import subprocess
import time

import boto3
import django
from bs4 import BeautifulSoup
from django.core.files import File

from common import util
from pruebas_app.models import Resultado
from pruebas_automaticas import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_app.settings")
django.setup()

SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_PUPPETEER = SQS.get_queue_by_name(QueueName=settings.SQS_PUPPETEER_NAME)

if __name__ == '__main__':
    while True:
        print('Entra ciclo')
        for message in COLA_PUPPETEER.receive_messages(MaxNumberOfMessages=1, MessageAttributeNames=['Id']):
            if message.message_attributes is not None:
                resultado_id = message.message_attributes.get('Id').get('StringValue')
                resultado = Resultado.objects.get(id=int(resultado_id))
                nuevo_archivo = util.copiar_contenido(resultado, settings.PUPPETEER_PATH,
                                                      settings.RUTAS_INTERNAS['Puppeteer'], '.test.js')

                comando = subprocess.run(['jest', nuevo_archivo], shell=True, stdout=subprocess.PIPE,
                                         cwd=settings.PUPPETEER_PATH)
                print('Salida:', comando.stdout.decode('utf-8'))
                print('returnCode', comando.returncode)
                reporte = open(settings.PUPPETEER_PATH + 'test-report.html', 'rb')
                archivo_reporte = File(reporte)
                # Si el returnCode es 0 es porque la prueba es exitosa
                if int(comando.returncode):
                    resultado.exitoso = False
                else:
                    resultado.exitoso = True
                resultado.resultado.save('reporte_puppeteer.html', archivo_reporte, save=True)
                resultado.terminada = True
                resultado.save()
                reporte.close()
                os.remove(reporte.name)
                os.remove(settings.PUPPETEER_PATH + nuevo_archivo)
                util.recoger_screenshoots(resultado)
                message.delete()
                util.validar_ultimo(resultado)
        time.sleep(settings.TIEMPO_ESPERA_WORKERS)
