import os

from django.db import models


# ------------------------------------------Primer mundo----------------------------------------------------------#


class TipoAplicacion(models.Model):
    tipo = models.CharField(max_length=30)

    def __str__(self):
        return '%s' % self.tipo


class Aplicacion(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField(verbose_name='descripción')
    tipo = models.ForeignKey(TipoAplicacion, on_delete=models.CASCADE)

    def __str__(self):
        return '%s' % self.nombre


def directorio_apk(instance, filename):
    # El script de la prueba sera subido a la carpeta archivos/scripts/(id de la estrategia)_(nombre del archivo)
    return 'apk/{0}_{1}_{2}'.format(instance.aplicacion.nombre, instance.numero, filename)


class Version(models.Model):
    numero = models.CharField(max_length=30)
    descripcion = models.TextField(verbose_name='descripción')
    aplicacion = models.ForeignKey(Aplicacion, on_delete=models.CASCADE)
    apk = models.FileField(upload_to=directorio_apk, null=True)
    url = models.CharField(max_length=200, null=True)
    nombre_paquete = models.CharField(max_length=100, null=True)

    def __str__(self):
        return '%s de la app: %s' % (self.numero, self.aplicacion.nombre)


class Estrategia(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField(verbose_name='descripción')
    aplicacion = models.ForeignKey(Aplicacion, on_delete=models.CASCADE)

    def __str__(self):
        return '%s' % self.nombre


class Herramienta(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField(verbose_name='descripción')

    def __str__(self):
        return '%s' % self.nombre


class Tipo(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField(verbose_name='descripción')

    def __str__(self):
        return '%s' % self.nombre


class Dispositivo(models.Model):
    device_definition = models.CharField(max_length=50)
    api_level = models.CharField(max_length=3)
    nombre_tecnico = models.CharField(max_length=50, blank=True)

    def save(self, *args, **kwargs):
        self.nombre_tecnico = "@"+self.device_definition.replace(" ", "_")+"_API_"+self.api_level
        super(Dispositivo, self).save(*args, **kwargs)

    def __str__(self):
        return '%s API %s' % (self.device_definition, self.api_level)


# ------------------------------------------Segundo mundo----------------------------------------------------------#


def directorio_script(instance, filename):
    # El script de la prueba sera subido a la carpeta archivos/scripts/(id de la estrategia)_(nombre del archivo)
    return 'scripts/{0}_{1}'.format(instance.estrategia.id, filename)


class Prueba(models.Model):
    script = models.FileField(upload_to=directorio_script, null=True)
    tipo = models.ForeignKey(Tipo, on_delete=models.CASCADE)
    estrategia = models.ForeignKey(Estrategia, on_delete=models.CASCADE)
    herramienta = models.ForeignKey(Herramienta, on_delete=models.CASCADE, null=True)
    numero_eventos = models.BigIntegerField(blank=True, null=True)

    @property
    def filename(self):
        return os.path.basename(self.script.path)

    def __str__(self):
        return 'Prueba id numero: %s de la estrategia: %s' % (self.id, self.estrategia.nombre)


def directorio_evidencia(instance, filename):
    # El script de la prueba sera subido a la carpeta archivos/scripts/(id de la estrategia)_(nombre del archivo)
    return 'evidencias/{0}_{1}'.format(instance.id, filename)


class Solicitud(models.Model):
    evidencia = models.FileField(upload_to=directorio_evidencia, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    estrategia = models.ForeignKey(Estrategia, on_delete=models.CASCADE)
    sensibilidad_VRT = models.DecimalField(null=True, max_digits=3, decimal_places=2)
    solicitud_VRT = models.ForeignKey('self', on_delete=models.CASCADE, null=True)
    version = models.ForeignKey(Version, on_delete=models.CASCADE)
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.CASCADE, null=True)

    def _pruebas_ejecutadas_(self):
        cantidad_total = self.resultado_set.all().count()
        cantidad_ejecutada = Resultado.objects.filter(terminada=True, solicitud=self).count()
        return '%s de %s' % (cantidad_ejecutada, cantidad_total)

    estado = property(_pruebas_ejecutadas_)

    def _solicitud_terminada_(self):
        cantidad_total = self.resultado_set.all().count()
        cantidad_ejecutada = Resultado.objects.filter(terminada=True, solicitud=self).count()
        return cantidad_total == cantidad_ejecutada

    terminada = property(_solicitud_terminada_)

    def _fallo_vrt_(self):
        fallo_vrt = ResultadoVRT.objects.filter(fallida=True, solicitud=self).count()
        if fallo_vrt > 0:
            resultado = "Cambios encontrados"
        else:
            resultado = "Sin cambios"
        return resultado

    resultado_vrt = property(_fallo_vrt_)

    def __str__(self):
        return 'Solicitud id numero: %s de la estrategia: %s estado: %s terminada %s' % (
            self.id, self.estrategia.nombre, self.estado, self.terminada)


def directorio_resultado(instance, filename):
    # El script de la prueba sera subido a la carpeta archivos/scripts/(id de la estrategia)_(nombre del archivo)
    return 'resultados/{0}_{1}_{2}'.format(instance.solicitud.id, instance.id, filename)


class Resultado(models.Model):
    resultado = models.FileField(upload_to=directorio_resultado, null=True)
    log = models.FileField(upload_to=directorio_resultado, null=True)
    terminada = models.BooleanField(default=False)
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE)
    prueba = models.ForeignKey(Prueba, on_delete=models.CASCADE)
    exitoso = models.BooleanField(default=False, null=True)

    def __str__(self):
        return '%s %s %s %s %s' % (self.resultado, self.log, self.terminada, self.solicitud, self.prueba)


def directorio_screenshots(instance, filename):
    # El script de la prueba sera subido a la carpeta archivos/scripts/(id de la estrategia)_(nombre del archivo)
    return 'screenshots/{0}_{1}_{2}'.format(instance.resultado.id, instance.id, filename)


class ScreenShot(models.Model):
    resultado = models.ForeignKey(Resultado, on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to=directorio_screenshots, null=True)
    nombre = models.CharField(max_length=30, null=True)

    def __str__(self):
        return '%s' % self.nombre


def directorio_vrt(instance, filename):
    return 'screenshots/VRT/{0}_{1}'.format(instance.solicitud.id, filename)


class ResultadoVRT(models.Model):
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE)
    screenshoot_previo = models.ImageField(upload_to=directorio_vrt, null=True)
    screenshoot_posterior = models.ImageField(upload_to=directorio_vrt, null=True)
    imagen_diferencias = models.ImageField(upload_to=directorio_vrt, null=True)
    fallida = models.BooleanField(default=False)
    informacion = models.CharField(max_length=200, null=True)
