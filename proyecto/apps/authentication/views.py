from .utils import generar_jwt, decodificar_jwt, get_datos_usuario, hash_password, validar_token
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Usuario
from .serializers import UsuarioSerializer
from django.core.serializers import serialize
from django.http import JsonResponse




@api_view(['POST'])
def registrar_usuario_api(request):
    data = request.data.copy()
    
    # Validación de campos obligatorios
    campos_requeridos = ['cedula', 'nombre', 'edad', 'celular', 'password']
    for campo in campos_requeridos:
        if campo not in data:
            return Response({"message": f"Falta el campo: {campo}"}, status=400)

    # Hash de contraseña
    data["password"] = hash_password(data["password"])

    serializer = UsuarioSerializer(data=data)
    if serializer.is_valid():
        if int(data.get("edad", 0)) < 0:
            return Response({"message": "Ingresa una edad válida"}, status=400)
        if Usuario.objects.filter(celular=data["celular"]).exists():
            return Response({"message": "El celular ya esta registrado"}, status=400)
        
        usuario = serializer.save() 

        return Response({"message": "Registro exitoso"}, status=201)
    
    return Response(serializer.errors, status=400)


@api_view(['POST'])
def validar_password_usuario_api(request):
    cedula = request.data.get("cedula")
    password = request.data.get("password")

    if not cedula or not password:
        return Response({"message": "Faltan la cédula o la contraseña"}, status=400)

    try:
        usuario = Usuario.objects.get(cedula=cedula)
    except Usuario.DoesNotExist:
        return Response({"message": "Usuario no encontrado"}, status=404)

    # Verificación directa desde Usuario
    password_bytes = password.encode('utf-8')
    stored_hash = usuario.password.encode('utf-8')
    
    if bcrypt.checkpw(password_bytes, stored_hash):
        return Response(generar_jwt(usuario.id), status=200)
    else:
        return Response({"message": "Contraseña incorrecta"}, status=401)


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
    id_usuario = request.query_params.get("id")  # <- viene por parámetro
    punto_atencion = request.data.get("punto_atencion")  # <- este sí viene en el body

    if not id_usuario or not punto_atencion:
        return Response({"message": "Faltan datos: id o punto de atención"}, status=400)

    try:
        usuario = Usuario.objects.get(pk=id_usuario)
        usuario.puntoAtencion = punto_atencion  # asegurate del nombre exacto del campo
        usuario.save()
        return Response({"message": "Punto de atención actualizado"}, status=200)
    except Usuario.DoesNotExist:
        return Response({"message": "Usuario no encontrado"}, status=404)
    except Exception as e:
        return Response({"message": "Error al actualizar el punto de atención", "error": str(e)}, status=500)

