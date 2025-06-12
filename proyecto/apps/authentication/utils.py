import jwt
from django.conf import settings
from datetime import datetime, timedelta
from .models import Usuario
from .serializers import UsuarioSerializer
from django.core.serializers import serialize
import bcrypt
import pyotp # Para autenticación de dos factores (opcional)

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
    
def validar_token(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ')[1] 
    payload = decodificar_jwt(token)
    return payload

def hash_password(password):
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')