from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from apps.authentication.models import Admin,Asesor, Usuario


#Tabla de puntos de atencion.
class PuntoAtencion(models.Model):
    nombre = models.CharField(max_length=100)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE, related_name='puntos_admin')
    asesor = models.ForeignKey(Asesor, on_delete=models.CASCADE, related_name='puntos_asesor')
    servicio_ofrecido = models.CharField(max_length=100)  # Puedes hacer una FK si quieres enlazar esto

    def __str__(self):
        return self.nombre

# Clase base abstracta para centralizar campos comunes
class ServicioBase(models.Model):
    prioritario = models.IntegerField(unique=True)
    general = models.IntegerField(unique=True)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    punto_atencion = models.ForeignKey(
        PuntoAtencion,
        on_delete=models.CASCADE,
        related_name='%(class)s_relacionados'  # ¡Solución clave!
    )
    
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

# Función para manejar el incremento y reinicio de campos
def manejar_campo_autoincremental(sender, instance, campo):
    if not getattr(instance, campo):  # Verifica si el campo está vacío
        ultimo_valor = sender.objects.aggregate(
            max_valor=models.Max(campo)
        )['max_valor']
        
        nuevo_valor = 1 if (ultimo_valor is None or ultimo_valor >= 100) else ultimo_valor + 1
        setattr(instance, campo, nuevo_valor)

# Señal genérica para manejar los campos prioritario y general
@receiver(pre_save)
def set_campos_autoincrementales(sender, instance, **kwargs):
    # Aplica solo a modelos que hereden de ServicioBase
    if issubclass(sender, ServicioBase):  
        instance.full_clean()
        for campo in ['prioritario', 'general']:  # Campos a manejar
            manejar_campo_autoincremental(sender, instance, campo)



