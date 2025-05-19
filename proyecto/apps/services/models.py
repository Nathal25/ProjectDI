from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from apps.authentication.models import Usuario

MAX_TURNO=100
# Clase base abstracta para centralizar campos comunes
class ServicioBase(models.Model):
    ESTADOS = [
        ('Pendiente', 'pendiente'),
        ('Atendido', 'atendido'),
        ('Pasado', 'pasado'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADOS, default='Pendiente')
    prioritario = models.IntegerField(unique=True,null=True, default=None, blank=True)
    general = models.IntegerField(unique=True,null=True, default=None, blank=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='%(class)s_turnos', null=True, blank=True)
    
    class Meta:
        abstract = True  # Define que esta clase no creará tabla en la base de datos

# Modelos específicos que heredan de la clase base
class ConsultaMedica(ServicioBase):
    def __str__(self):
        return "Consulta Médica"

class ReclamarMedicamentos(ServicioBase):
    def __str__(self):
        return "Reclamar Medicamentos"

class Asesoramiento(ServicioBase):
    def __str__(self):
        return "Asesoramiento"

# Lógica para asignar turnos (sin punto de atención)
def obtener_siguiente_turno(modelo, campo):
    turnos = modelo.objects.values_list(campo, flat=True)
    turnos_existentes = [t for t in turnos if t is not None]
    
    if not turnos_existentes:
        return 1

    max_turno = max(turnos_existentes)
    return 1 if max_turno >= MAX_TURNO else max_turno + 1

@receiver(pre_save, sender=ConsultaMedica)
@receiver(pre_save, sender=ReclamarMedicamentos)
@receiver(pre_save, sender=Asesoramiento)
def asignar_turnos(sender, instance, **kwargs):
    if not instance.estado:
        instance.estado = 'Pendiente'
    if instance.usuario:
        if not instance.prioritario and not instance.general:
            if instance.usuario.discapacidad or instance.usuario.embarazo:
                instance.prioritario = obtener_siguiente_turno(sender, "prioritario")
            else:
                instance.general = obtener_siguiente_turno(sender, "general")

 