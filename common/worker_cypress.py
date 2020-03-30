import os
import subprocess
import boto3
import django
import time
from django.core.files import File
from common import util
from pruebas_automaticas import settings
from pruebas_app.models import Resultado
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_app.settings")
django.setup()


SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_CYPRESS = SQS.get_queue_by_name(QueueName=settings.SQS_CYPRESS_NAME)

if __name__ == '__main__':
    while True:
        print('Entra ciclo')
        for message in COLA_CYPRESS.receive_messages(MaxNumberOfMessages=1, MessageAttributeNames=['Id']):
            if message.message_attributes is not None:

                resultado_id = message.message_attributes.get('Id').get('StringValue')
                resultado = Resultado.objects.get(id=int(resultado_id))
    
                nuevo_archivo = util.copiar_contenido(resultado, settings.CYPRESS_PATH, settings.RUTAS_INTERNAS["Cypress"], '.js')

                salida = subprocess.call(['npx', 'cypress', 'run', 'cypress:run', '--spec', nuevo_archivo], shell=True, cwd=settings.CYPRESS_PATH)

                print('La salida es:', salida)

                video = open(settings.CYPRESS_PATH+'//cypress//videos//'+str(resultado.id)+'.js.mp4', 'rb')
                archivo_video = File(video)
                resultado.resultado.save('cypress.mp4', archivo_video, save=True)
                resultado.terminada = True
                resultado.save()
                video.close()
                message.delete()
                util.validar_ultimo(resultado.solicitud)
        time.sleep(settings.TIEMPO_ESPERA_WORKERS)
