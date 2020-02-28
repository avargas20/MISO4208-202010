from django.db import models

# Primer mundo

class Aplicacion(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField(verbose_name='descripción')
    TIPOS = (
    ("movil", "móvil"),
    ("web", "web"), 
            )     
    tipo = models.CharField(max_length=10, choices=TIPOS)

    def __str__(self):
        return '%s' % self.nombre

class Version(models.Model):
    numero = models.CharField(max_length=30)
    descripcion = models.TextField(verbose_name='descripción')
    aplicacion = models.ForeignKey(Aplicacion, on_delete=models.CASCADE)

    def __str__(self):
        return '%s de la app: %s' % (self.numero, self.aplicacion.nombre)

class Estrategia(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField(verbose_name='descripción')
    version = models.ForeignKey(Version, on_delete=models.CASCADE)

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

def directorio_script(instance, filename):
    # El script de la prueba sera subido a la carpeta archivos/scripts/(id de la estrategia)_(nombre del archivo)
    return 'scripts/{0}_{1}'.format(instance.estrategia.id, filename)

class Prueba(models.Model):
    script = models.FileField(upload_to=directorio_script)
    tipo = models.ForeignKey(Tipo, on_delete=models.CASCADE)
    estrategia = models.ForeignKey(Estrategia, on_delete=models.CASCADE)
    herramienta = models.ForeignKey(Herramienta, on_delete=models.CASCADE)

    def __str__(self):
        return 'Prueba id numero: %s de la estrategia: %s' % (self.id, self.estrategia.nombre)

class Estado(models.Model):
    descripcion = models.CharField(max_length=50)

class Solicitud(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    estrategia = models.ForeignKey(Estrategia, on_delete=models.CASCADE)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)

    def __str__(self):
        return 'Solicitud id numero: %s de la estrategia: %s' % (self.id, self.estrategia.nombre)

def directorio_resultado(instance, filename):
    # El script de la prueba sera subido a la carpeta archivos/scripts/(id de la estrategia)_(nombre del archivo)
    return 'resultados/{0}_{1}_{2}'.format(instance.solicitud.id, instance.id, filename)

class Resultado(models.Model):
    resultado = models.FileField(upload_to=directorio_resultado)
    terminada = models.BooleanField(default=False)
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE)
    prueba = models.ForeignKey(Prueba, on_delete=models.CASCADE)

