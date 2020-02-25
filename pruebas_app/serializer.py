from .models import *

from rest_framework import serializers


class AplicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aplicacion

        fields = ('nombre', 'tipo')


class VersionSerializer(serializers.ModelSerializer):
    aplicacion = AplicacionSerializer()

    class Meta:
        model = Version

        fields = ('numero', 'aplicacion')


class EstrategiaSerializer(serializers.ModelSerializer):
    version = VersionSerializer()

    class Meta:
        model = Estrategia

        fields = ('nombre', 'descripcion', 'version')


class SolicitudSerializer(serializers.ModelSerializer):
    estrategia = EstrategiaSerializer()

    class Meta:
        model = Solicitud

        fields = ('id', 'fecha', 'estrategia')
