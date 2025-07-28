from rest_framework import serializers
from .models import Announcement
from apps.authentication.models import Usuario

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['url', 'title']

class UsuarioListadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['nombre', 'cedula', 'correo', 'rol','active']