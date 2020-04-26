import os
import subprocess
import boto3
import django
import time
from django.core.files import File
from common import util
from pruebas_automaticas import settings
from pruebas_app.models import Mutacion, Mutante, Operador
from shutil import copyfile, copy

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
                util.configurar_archivo_operadores(mutacion)
                util.limpiar_folder(os.path.join(settings.MUTAPK_PATH, settings.RUTAS_INTERNAS2.Mutacion.value))
                # Copio el archivo apk de la version a la ruta de MutAPK para que la tome desde alli el comando
                copyfile(mutacion.version.apk.path, os.path.join(settings.MUTAPK_PATH, mutacion.version.apk.name))
                # La propiedad name del filefield tiene apk/nombre.apk, tuve que cambiar el / por \\ para que el
                # comando funcionara
                ruta_apk = mutacion.version.apk.name.replace('/', '\\')
                comando = 'java -jar target\\MutAPK-0.0.1.jar {0} {1} mutants\\ extra\\ properties\\ true {2}'.format(
                    ruta_apk, mutacion.version.nombre_paquete, str(mutacion.numero_mutantes))
                salida = subprocess.call(comando, shell=True, cwd=settings.MUTAPK_PATH)
                print('La salida es:', salida)
                util.recoger_reportes_mutacion(mutacion)
                util.recoger_mutantes(mutacion)
                message.delete()

        time.sleep(settings.TIEMPO_ESPERA_WORKERS)
