from rest_framework import serializers 
from .models import Truno

class TurnoSerializer(serializers.ModelSerializer):
    codigo = serializers.SerializerMethodField()

    class Meta:
        model = Turno
        fields = [ 'id', 'prioridad', 'numero', 'servicio', 'puntoAtencion', 'codigo']
    
    def get_codigo(self, obj):
        return f"{obj.prioridad}{str(obj.numero).zfill(2)}{obj.servicio}"