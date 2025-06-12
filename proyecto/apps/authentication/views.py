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


@ratelimit(key='post:cedula', rate=settings.LOGIN_RATE_LIMIT, method='POST', block=False)
@api_view(['POST'])
def validar_password_usuario_api(request):
    if getattr(request, 'limited', False):
        return Response(
            {"message": "Demasiados intentos. Intenta de nuevo más tarde."},
            status=429
        )

    cedula = request.data.get('cedula')
    password = request.data.get('password')
    totp_code = request.data.get('totp')

    if not cedula or not password or not totp_code:
        return Response({"message": "Faltan la cédula, la contraseña o el código TOTP"}, status=400)

    try:
        usuario = Usuario.objects.get(cedula=cedula)
    except Usuario.DoesNotExist:
        return Response({"message": "Usuario no encontrado"}, status=404)

    # Verificación de bloqueo por intentos fallidos de TOTP
    if usuario.totp_locked_until and usuario.totp_locked_until > timezone.now():
        return Response(
            {"message": "Cuenta bloqueada por intentos fallidos. Intenta más tarde."},
            status=403
        )

    # Verificación de contraseña
    password_bytes = password.encode('utf-8')
    stored_hash = usuario.password.encode('utf-8')
    if not bcrypt.checkpw(password_bytes, stored_hash):
        return Response({"message": "Contraseña incorrecta"}, status=401)

    # Verificación TOTP
    totp = pyotp.TOTP(usuario.totp_secret)
    if not totp.verify(totp_code):
        usuario.totp_failed_attempts += 1
        if usuario.totp_failed_attempts >= 3:
            usuario.totp_locked_until = timezone.now() + timedelta(minutes=3)
        usuario.save()
        return Response({"message": "Código TOTP inválido"}, status=401)
    else:
        # Reiniciar contador de intentos y desbloquear al acertar
        usuario.totp_failed_attempts = 0
        usuario.totp_locked_until = None
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


@api_view(['POST'])
def verificar_totp(request):
    cedula = request.data.get('cedula')
    code = request.data.get('code')

    if not cedula or not code:
        return Response({"message": "Faltan la cédula o el código"}, status=400)

    try:
        usuario = Usuario.objects.get(cedula=cedula)
        usuario.totp_secret= code
        usuario.totp_confirmed = True
        usuario.save()
        return Response({"message": "TOTP activado exitosamente"})
    except Usuario.DoesNotExist:
        return Response({"message": "Usuario no encontrado"}, status=404)

