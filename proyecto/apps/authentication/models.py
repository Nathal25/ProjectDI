from django.db import models

class Usuario(models.Model):
    ROLES = [
        ('admin', 'Admin'),
        ('paciente', 'Paciente'),
        ('asesor', 'Asesor'),
    ]

    cedula = models.IntegerField(unique=True)  
    nombre = models.CharField(max_length=128)
    edad = models.IntegerField()  
    celular = models.CharField(max_length=10) 
    sexo = models.CharField(max_length=10, choices=[('m', 'M'), ('f', 'F')], default='m')
    correo = models.EmailField(max_length=254, unique=True, null=True)
    rol = models.CharField(max_length=50, choices=ROLES, default='paciente')  # Cambié 'user' por 'paciente' ya que 'user' no está en choices

    def __str__(self):
        return self.nombre  # Arreglado (antes era self.username, pero no existe ese campo)

class Paciente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    condEspecial = models.CharField(max_length=128, null=True)

    def __str__(self):
        return self.usuario.nombre  # Arreglado

class Asesor(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.usuario.nombre  # Arreglado

class Admin(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.usuario.nombre  # Arreglado
