import os
import subprocess
import boto3
import django
import time
from django.core.files import File
from common import util
from pruebas_automaticas import settings
from pruebas_app.models import Mutacion, Mutante, Operador

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_app.settings")
django.setup()

SQS = boto3.resource('sqs', region_name='us-east-1')
COLA_MUTACION = SQS.get_queue_by_name(QueueName=settings.SQS_MUTACION_NAME)

if __name__ == '__main__':
    while True:
        print('Entra ciclo')
        for message in COLA_MUTACION.receive_messages(MaxNumberOfMessages=1, MessageAttributeNames=['Id']):
            if message.message_attributes is not None:
                mutacion_id = message.message_attributes.get('Id').get('StringValue')
                mutacion = Mutacion.objects.get(id=int(mutacion_id))
                message.delete()

        time.sleep(settings.TIEMPO_ESPERA_WORKERS)
