import jwt
from django.conf import settings
from datetime import datetime, timedelta
from .models import Admin, Asesor, Paciente, Usuario
from .serializers import UsuarioSerializer
from django.core.serializers import serialize

def generar_jwt(usuario_id):
    payload = {
        'usuario_id': usuario_id,
        'exp': datetime.utcnow() + timedelta(hours=24),  # Token válido por 24h
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

def decodificar_jwt(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_datos_usuario(usuario_id):
    try:
        usuario = Usuario.objects.get(id=usuario_id)
        serializer = UsuarioSerializer(usuario)
        return serializer.data
    except Usuario.DoesNotExist:
        return None