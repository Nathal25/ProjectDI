from .utils import generar_jwt, decodificar_jwt, get_datos_usuario
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Admin, Asesor, Paciente, Usuario
from .serializers import UsuarioSerializer
from django.core.serializers import serialize
from django.http import JsonResponse
import json

@api_view(['POST'])
def registrar_usuario_api(request):
    serializer = UsuarioSerializer(data=request.data)
    if serializer.is_valid():
        if request.data.get("edad") < 0:
            return Response({"message": "Ingresa una edad valida"}, status=400)
        usuario = serializer.save()
        Paciente.objects.create(usuario=usuario)
        return Response({"message": "Registro exitoso"}, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def identifier_usuario_api(request):
    cedula = request.data.get("cedula")  # verifica si existe la cedula
    usuario = Usuario.objects.filter(cedula=cedula)
    if Usuario.objects.filter(cedula=cedula).exists():
    # Serializar el QuerySet a JSON
        usuarios_json = serialize('json', usuario)
        usuarios_data = json.loads(usuarios_json)
        if usuario[0].rol == "admin" or  usuario[0].rol == "asesor":
           return Response({"message": "Usuario requiere contraseña", 
                            "data": usuarios_data[0]['fields']['cedula']}, status=400)
        # Convertir la cadena JSON en un objeto Python
        fields_list = [item['fields'] for item in usuarios_data]
        # Retornar el objeto JSON
        return Response(fields_list, status=200)

    return Response({"message": "Usuario no esta regristrado"}, status=201)

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

    if usuario.rol == "admin":
        try:
            admin = Admin.objects.get(usuario=usuario)
            if admin.password == password:
                admin_json = serialize('json', [admin])
                admin_data = json.loads(admin_json)
                usuario_id = admin_data[0]['fields']['usuario']
                return Response(generar_jwt(usuario_id), status=200)
            else:
                return Response({"message": "Contraseña incorrecta para administrador"}, status=401)
        except Admin.DoesNotExist:
            return Response({"message": "Este usuario no tiene datos de administrador"}, status=404)

    elif usuario.rol == "asesor":
        try:
            asesor = Asesor.objects.get(usuario=usuario)
            if asesor.password == password:
                asesor_json = serialize('json', [asesor])
                asesor_data = json.loads(asesor_json)
                usuario_a_id = asesor_data[0]['fields']['usuario']
                return Response(generar_jwt(usuario_a_id), status=200)
            else:
                return Response({"message": "Contraseña incorrecta para asesor"}, status=401)
        except Asesor.DoesNotExist:
            return Response({"message": "Este usuario no tiene datos de asesor"}, status=404)

    else:
        return Response({"message": "No se encontro el rol del usuario"}, status=400)
    

@api_view(['GET'])  # Cambiamos a GET porque los tokens no se mandan por POST
def validar_token_api(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({"message": "Token no proporcionado o mal formado"}, status=400)

    token = auth_header.split(' ')[1]  # Obtenemos el token después de "Bearer"
    payload = decodificar_jwt(token)

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

