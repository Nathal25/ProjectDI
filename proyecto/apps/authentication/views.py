from .utils import generar_jwt, decodificar_jwt, get_datos_usuario, hash_password, validar_token
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Usuario
from .serializers import UsuarioSerializer
from django.core.serializers import serialize
from django.http import JsonResponse
from django.utils.html import escape
from django.conf import settings
from django_ratelimit.decorators import ratelimit
import bcrypt
import pyotp
import qrcode
from io import BytesIO
import base64
from django.utils import timezone
from datetime import timedelta
import uuid

TEMP_TOKENS = {}

@api_view(['POST'])
def registrar_usuario_api(request):
    data = request.data.copy()
    
    # Validación de campos obligatorios
    campos_requeridos = ['cedula', 'nombre', 'edad', 'celular', 'password']
    for campo in campos_requeridos:
        if campo not in data:
            return Response({"message": f"Falta el campo: {campo}"}, status=400)

    # Escapar campos texto libre
    data["nombre"] = escape(data["nombre"])
    if "correo" in data:
        data["correo"] = escape(str(data["correo"]))
    data["celular"] = escape(data["celular"])  # si se acepta texto con símbolos
    
    # Hash de contraseña
    data["password"] = hash_password(data["password"])

    serializer = UsuarioSerializer(data=data)
    if serializer.is_valid():
        if int(data.get("edad", 0)) < 0:
            return Response({"message": "Ingresa una edad válida"}, status=400)
        if Usuario.objects.filter(celular=data["celular"]).exists():
            return Response({"message": "El celular ya esta registrado"}, status=400)
        
        
        usuario = serializer.save() 
        # Generar TOTP automáticamente al registrar
        usuario.totp_secret = pyotp.random_base32()
        usuario.totp_confirmed = True  

        usuario.save()  # Guardar el usuario con el TOTP generado
        # Generar QR para Google Authenticator
        totp = pyotp.TOTP(usuario.totp_secret)
        uri = totp.provisioning_uri(name=usuario.correo, issuer_name="SAMU")
        qr = qrcode.make(uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return Response({
            "message": "Registro exitoso",
            "qr": qr_base64,
            "secret": usuario.totp_secret
        }, status=201)
    
    return Response(serializer.errors, status=400)


#@ratelimit(key='post:cedula', rate=settings.LOGIN_RATE_LIMIT, method='POST', block=False)
@api_view(['POST'])
def validar_password_usuario_api(request):
    
    cedula = request.data.get('cedula')
    password = request.data.get('password')

    if not cedula or not password:
        return Response({"message": "Faltan la cédula o la contraseña"}, status=400)

    try:
        usuario = Usuario.objects.get(cedula=cedula)
    except Usuario.DoesNotExist:
        return Response({"message": "Usuario no encontrado"}, status=404)
    
    # Verificar si el usuario está bloqueado
    if usuario.locked_until and usuario.locked_until > timezone.now():
        tiempo_restante = int((usuario.locked_until - timezone.now()).total_seconds() // 60) + 1
        return Response({
            'message': f'Usuario bloqueado por demasiados intentos fallidos. Intenta de nuevo en {tiempo_restante} minutos.'
        }, status=423)
    # Verificación de contraseña
    # Verificar contraseña
    password_bytes = password.encode('utf-8')
    stored_hash = usuario.password.encode('utf-8')
    if not bcrypt.checkpw(password_bytes, stored_hash):
        usuario.failed_login_attempts += 1
        intentos_restantes = settings.LOGIN_FAILS_LIMIT - usuario.failed_login_attempts
        if usuario.failed_login_attempts >= settings.LOGIN_FAILS_LIMIT:
            usuario.locked_until = timezone.now() + timedelta(seconds=settings.LOGIN_FAILS_TIMEOUT)
            usuario.save()
            return Response({
                'message': 'Usuario bloqueado por demasiados intentos fallidos. Intenta de nuevo más tarde.'
            }, status=423)
        usuario.save()
        return Response({
            'message': 'Contraseña incorrecta.',
            'intentos_restantes': max(0, intentos_restantes)
        }, status=401)
    # Reiniciar contadores de intentos fallidos
    usuario.failed_login_attempts = 0
    usuario.locked_until = None
    usuario.save()
    # Todo correcto: generar y devolver el JWT
    return Response(generar_jwt(usuario.id), status=200)

@api_view(['GET'])  # Cambiamos a GET porque los tokens no se mandan por POST
def validar_token_api(request):
    payload = validar_token(request)
    if not payload:
        return Response({"message": "Token inválido o no proporcionado"}, status=401)

    if payload:
        usuario_id = payload.get("usuario_id")
        datos_usuario = get_datos_usuario(usuario_id)
        return Response({"message": "Token válido", "data": datos_usuario}, status=200)
    else:
        return Response({"message": "Token inválido o expirado"}, status=401)

@api_view(['POST'])
def cambiar_punto_atencion(request):
    # Extraer y validar token
    payload = validar_token(request)
    if not payload:
        return Response({"message": "Token inválido o no proporcionado"}, status=401)
    
    id_usuario = payload.get("usuario_id")  # Extraer el id del payload del token
    punto_atencion = request.data.get("punto_atencion")
    
    if not punto_atencion:
        return Response({"message": "Falta el punto de atención"}, status=400)
    
    try:
        usuario = Usuario.objects.get(pk=id_usuario)
        usuario.puntoAtencion = escape(punto_atencion)
        usuario.save()
        return Response({"message": "Punto de atención actualizado"}, status=200)
    except Usuario.DoesNotExist:
        return Response({"message": "Usuario no encontrado"}, status=404)
    except Exception as e:
        return Response({"message": "Error al actualizar el punto de atención", "error": str(e)}, status=500)

# This endpoint is used to verify the identity of the user using TOTP
# It checks the user's cedula and TOTP code, and if successful, 
# generates a temporary token for password restoration.
@api_view(['POST'])
def verify_identity(request):
    cedula = request.data.get('cedula')
    totp_code = request.data.get('totp')

    if not cedula or not totp_code:
        return Response({"message": "Cédula y TOTP son obligatorios"}, status=400)

    usuario = Usuario.objects.filter(cedula=cedula).first()
    if not usuario:
        return Response({"message": "Usuario no encontrado"}, status=404)

    # Verifica bloqueo por intentos fallidos
    if usuario.totp_locked_until and usuario.totp_locked_until > timezone.now():
        return Response({"message": "Demasiados intentos fallidos. Intente más tarde."}, status=403)

    totp = pyotp.TOTP(usuario.totp_secret)
    if not totp.verify(totp_code):
        usuario.totp_failed_attempts += 1
        if usuario.totp_failed_attempts >= 3:
            usuario.totp_locked_until = timezone.now() + timedelta(minutes=3)
        usuario.save()
        return Response({"message": "Código TOTP inválido"}, status=401)

    # Si todo está bien, genera token temporal
    temp_token = str(uuid.uuid4())
    TEMP_TOKENS[temp_token] = {'cedula': cedula, 'expires': timezone.now() + timedelta(minutes=10)}
    usuario.totp_failed_attempts = 0
    usuario.totp_locked_until = None
    usuario.save()
    return Response({"temp_token": temp_token, 
                     "message": "Identidad verificada. Ahora ingrese la nueva contraseña."
                     })

# This endpoint is used to restore the password using a temporary token
# It checks the temporary token and updates the user's password if valid.
@api_view(['POST'])
def restore_password(request):
    temp_token = request.data.get('temp_token')
    new_password = request.data.get('new_password')

    if not temp_token or not new_password:
        return Response({"message": "Token temporal y nueva contraseña son obligatorios"}, status=400)

    token_data = TEMP_TOKENS.get(temp_token)
    if not token_data or token_data['expires'] < timezone.now():
        return Response({"message": "Token inválido o expirado"}, status=401)

    usuario = Usuario.objects.filter(cedula=token_data['cedula']).first()
    if not usuario:
        return Response({"message": "Usuario no encontrado"}, status=404)

    usuario.password = hash_password(new_password)
    usuario.save()
    # Elimina el token temporal
    del TEMP_TOKENS[temp_token]
    return Response({"message": "Contraseña actualizada exitosamente"})
    

