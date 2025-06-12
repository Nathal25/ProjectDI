from django.db import models
from django.core.validators import RegexValidator

class Usuario(models.Model):
    ROLES = [
        ('admin', 'Admin'),
        ('paciente', 'Paciente'),
        ('asesor', 'Asesor'),
    ]
    
    PUNTOSATENCION = [
        ('sur', 'Sur'),
        ('centro', 'Centro'),
        ('norte', 'Norte')
    ]

    CONDICIONESPRIORITARIAS=[
        ('adulto de la tercera edad','Tercera-edad'),
        ('discapacidad fisica permanente', 'Discapacidad-fisica-permanente'),
        ('discapacidad mental permanente', 'Discapacidad-mental-permanente'),
    ]
    
    cedula = models.IntegerField(unique=True)  
    nombre = models.CharField(max_length=128)
    edad = models.IntegerField()  
    celular = models.CharField(max_length=10, unique=True,
                               validators=[
                                RegexValidator(
                                regex=r'^\d{10}$',
                                message="El número de celular debe tener exactamente 10 dígitos y no puede ser negativo."
            )
        ])
    puntoAtencion = models.CharField(max_length=10, choices=PUNTOSATENCION, default='sur') 
    sexo = models.CharField(max_length=10, choices=[('m', 'M'), ('f', 'F')], default='m')
    correo = models.EmailField(max_length=254, unique=True, null=True)
    rol = models.CharField(max_length=50, choices=ROLES, default='paciente')  # Cambié 'user' por 'paciente' ya que 'user' no está en choices
    discapacidad = models.CharField(max_length=50, choices=CONDICIONESPRIORITARIAS, null=True,default=None)
    password = models.CharField(max_length=128, null=True, blank=True)  # Agregado para almacenar la contraseña del usuario
    
    totp_secret = models.CharField(max_length=32, blank=True, null=True)
    totp_confirmed = models.BooleanField(default=False)
    totp_failed_attempts = models.PositiveIntegerField(default=0)
    totp_locked_until = models.DateTimeField(null=True)
    
    def __str__(self):
        return self.nombre  # Arreglado (antes era self.username, pero no existe ese campo)
    
