from rest_framework import serializers
from .models import Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'cedula', 'nombre', 'edad', 'celular', 'puntoAtencion', 
            'sexo', 'correo', 'rol', 'discapacidad', 'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'celular': {'validators': []}  # Desactiva validación duplicada
        }

