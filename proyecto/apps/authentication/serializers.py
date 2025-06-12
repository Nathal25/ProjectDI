from rest_framework import serializers
from .models import Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'cedula', 'nombre', 'edad', 'celular', 'puntoAtencion', 
            'sexo', 'correo', 'rol', 'discapacidad', 'password',
            'totp_secret', 'totp_confirmed'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            # Mantén los validadores del modelo para 'celular':
            'celular': {'validators': []}  # Solo si necesitas desactivar validadores adicionales
        }




