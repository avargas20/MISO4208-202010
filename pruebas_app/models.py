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

class Version(models.Model):
    numero = models.CharField(max_length=30)
    descripcion = models.TextField(verbose_name='descripción')
    aplicacion = models.ForeignKey(Aplicacion, on_delete=models.CASCADE)

class Estrategia(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField(verbose_name='descripción')
    version = models.ForeignKey(Version, on_delete=models.CASCADE)

class Herramienta(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField(verbose_name='descripción')

class Tipo(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField(verbose_name='descripción')

class Prueba(models.Model):
    script = models.FileField(upload_to='scripts/')
    tipo = models.ForeignKey(Tipo, on_delete=models.CASCADE)
    estrategia = models.ForeignKey(Estrategia, on_delete=models.CASCADE)
    herramienta = models.ForeignKey(Herramienta, on_delete=models.CASCADE)
