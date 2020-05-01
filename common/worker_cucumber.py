import os
import shutil
import subprocess
import time

import boto3
import django
from django.core.files import File

from common import util
from pruebas_app.models import Resultado
from pruebas_automaticas import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_app.settings")
django.setup()

SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_CUCUMBER = SQS.get_queue_by_name(QueueName=settings.SQS_CUCUMBER_NAME)

if __name__ == '__main__':
    while True:
        print('Entra ciclo')
        for message in COLA_CUCUMBER.receive_messages(MaxNumberOfMessages=1, MessageAttributeNames=['Id']):
            if message.message_attributes is not None:
                resultado_id = message.message_attributes.get('Id').get('StringValue')
                resultado = Resultado.objects.get(id=int(resultado_id))
                nuevo_feature = util.copiar_contenido(resultado, settings.CUCUMBER_PATH,
                                                      settings.RUTAS_INTERNAS["CucumberFeatures"], '.feature')
                try:
                    salida = subprocess.check_call('npm test', shell=True, cwd=settings.CUCUMBER_PATH)
                    resultado.exitoso = True
                except:
                    print("Fallo")
                    resultado.exitoso = False

                shutil.make_archive(settings.BASE_DIR + '//evidencias', 'zip',
                                    settings.CUCUMBER_PATH + settings.RUTAS_INTERNAS["CucumberReporte"])

                reporte = open(settings.BASE_DIR + '//evidencias.zip', 'rb')
                archivo_reporte = File(reporte)
                resultado.resultado.save('reporte_cucumber.zip', archivo_reporte, save=True)
                resultado.terminada = True
                resultado.save()
                reporte.close()
                os.remove(reporte.name)
                script_path = settings.CUCUMBER_PATH + "/" + nuevo_feature
                os.remove(script_path)
                message.delete()
                util.validar_ultimo(resultado.solicitud)
        time.sleep(settings.TIEMPO_ESPERA_WORKERS)
