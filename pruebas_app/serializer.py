from rest_framework import serializers

from .models import *


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


class EstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estado

        fields = '__all__'


class SolicitudSerializer(serializers.ModelSerializer):
    estrategia = EstrategiaSerializer()
    estado = EstadoSerializer()

    class Meta:
        model = Solicitud

        fields = ('id', 'fecha', 'estrategia', 'estado')
