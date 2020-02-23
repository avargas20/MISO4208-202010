from pruebas_automaticas import settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pruebas_app.settings")
django.setup()

from pruebas_app.models import Aplicacion, Prueba, Version, Herramienta, Tipo, Estrategia, Solicitud, Resultado


def funcion(resultado_id):
    
    print(resultado_id)