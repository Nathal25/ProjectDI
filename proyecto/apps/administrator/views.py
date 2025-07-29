from apps.authentication.models import Usuario
from apps.authentication.serializers import UsuarioSerializer
from .serializer import AnnouncementSerializer, UsuarioListadoSerializer
from apps.authentication.utils import hash_password, validar_token
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.authentication.utils import get_datos_usuario
from .models import Announcement


@api_view(['POST'])
def crear_asesor_admin(request):
    data = request.data.copy()
    payload = validar_token(request)
    if not payload:
        return Response({"message": "Token inválido o no proporcionado"}, status=401)
    
    # Validación de campos obligatorios
    campos_requeridos = ['cedula', 'nombre', 'edad', 'celular', 'password', 'rol']
    for campo in campos_requeridos:
        if campo not in data:
            return Response({"message": f"Falta el campo: {campo}"}, status=400)

    if payload:
        usuario_id = payload.get("usuario_id")
        datos_usuario = get_datos_usuario(usuario_id)
        if datos_usuario and datos_usuario.get("rol") == "admin":
            data["password"] = hash_password(data["password"])
            serializer = UsuarioSerializer(data=data)
            if serializer.is_valid():
                if int(data.get("edad", 0)) < 0:
                    return Response({"message": "Ingresa una edad válida"}, status=400)
                if Usuario.objects.filter(celular=data["celular"]).exists():
                    return Response({"message": "El celular ya está registrado"}, status=400)
                
                usuario = serializer.save()
            
            return Response({"message": "Asesor creado exitosamente"}, status=201)
        else:
            return Response({"message": "No tienes permisos para crear un asesor"}, status=403)
        

@api_view(['POST'])
def subir_anuncio(request):
    data = request.data.copy()
    payload = validar_token(request)
    if not payload:
        return Response({"message": "Token inválido o no proporcionado"}, status=401)
    
    # Validación de campos obligatorios
    campos_requeridos = ['url', 'title']
    for campo in campos_requeridos:
        if campo not in data:
            return Response({"message": f"Falta el campo: {campo}"}, status=400)

    if payload:
        usuario_id = payload.get("usuario_id")
        datos_usuario = get_datos_usuario(usuario_id)
        if datos_usuario and datos_usuario.get("rol") == "admin":
            if data.get("url") and not data.get("url").endswith("jpg") and not data.get("url").endswith("png"):
                return Response({"message": "La URL debe terminar en .jpg o .png"}, status=400)
            serializer = AnnouncementSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=400)           
            return Response({"message": "Anuncio subido exitosamente"}, status=201)
        else:
            return Response({"message": "No tienes permisos para subir un anuncio"}, status=403)
        

@api_view(['GET'])
def traer_anuncios(request):
    anuncios = AnnouncementSerializer(Announcement.objects.all(), many=True)
    return Response(anuncios.data, status=200)
    

@api_view(['DELETE'])
def borrar_anuncio(request):
    data = request.data.copy()
    payload = validar_token(request)
    if not payload:
        return Response({"message": "Token inválido o no proporcionado"}, status=401)
    
    # Validación de campos obligatorios
    if 'title' not in data:
        return Response({"message": "Falta el campo: titulo"}, status=400)

    if payload:
        usuario_id = payload.get("usuario_id")
        datos_usuario = get_datos_usuario(usuario_id)
        if datos_usuario and datos_usuario.get("rol") == "admin":
            try:
                anuncio = Announcement.objects.get(title=data["title"])
                anuncio.delete()
                return Response({"message": "Anuncio borrado exitosamente"}, status=200)
            except Announcement.DoesNotExist:
                return Response({"message": "Anuncio no encontrado"}, status=404)
        else:
            return Response({"message": "No tienes permisos para borrar un anuncio"}, status=403)
      
@api_view(['DELETE'])
def eliminar_usuario(request):
    payload = validar_token(request)
    if not payload:
        return Response({"error": "Token inválido o expirado"}, status=401)

    usuario_id = payload.get("usuario_id")
    if not usuario_id:
        return Response({"error": "Token inválido"}, status=401)

    try:
        usuario = Usuario.objects.get(pk=usuario_id)
    except Usuario.DoesNotExist:
        return Response({"error": "Usuario no encontrado en base de datos"}, status=404)

    if usuario.rol != 'admin':
        return Response({"error": "No tienes permiso para modificar turnos"}, status=403)

    cedula = request.data.get("cedula")

    if not cedula:
        return Response({"error": "Debes proporcionar la cédula del usuario a eliminar"}, status=400)
    
    try:
        usuario_eliminar = Usuario.objects.get(cedula=cedula)
        usuario_eliminar.delete()
        return Response({"mensaje": f"usuario con cedula {cedula} eliminado correctamente"}, status=200)
    except Usuario.DoesNotExist:
        return Response({"error": "uduario no encontrado con esa cedula"}, status=400)
    
# This endpoint is used to list all users in the same point of attention as the admin user
# It checks the user's role and point of attention, and returns a list of users with roles
@api_view(['GET'])
def list_users_by_puntoA(request):
    payload = validar_token(request)
    if not payload:
        return Response({"message": "Token inválido o no proporcionado"}, status=401)

    usuario_id = payload.get("usuario_id")
    if not usuario_id:
        return Response({"message": "Token inválido"}, status=401)

    try:
        admin_usuario = Usuario.objects.get(pk=usuario_id)
    except Usuario.DoesNotExist:
        return Response({"message": "Usuario admin no encontrado"}, status=404)

    if admin_usuario.rol != 'admin':
        return Response({"message": "No tienes permisos para listar usuarios"}, status=403)

    usuarios = Usuario.objects.filter(
        puntoAtencion=admin_usuario.puntoAtencion,
        rol__in=['paciente', 'asesor']
    )

    serializer = UsuarioListadoSerializer(usuarios, many=True)
    return Response(serializer.data, status=200)

@api_view(['POST'])
def deactive_user(request):
    payload = validar_token(request)
    if not payload:
        return Response({"message": "Token inválido o no proporcionado"}, status=401)

    usuario_id = payload.get("usuario_id")
    if not usuario_id:
        return Response({"message": "Token inválido"}, status=401)

    try:
        admin_usuario = Usuario.objects.get(pk=usuario_id)
    except Usuario.DoesNotExist:
        return Response({"message": "Usuario admin no encontrado"}, status=404)

    if admin_usuario.rol != 'admin':
        return Response({"message": "No tienes permisos para inactivar usuarios"}, status=403)

    cedula = request.data.get("cedula")
    if not cedula:
        return Response({"message": "Debes proporcionar la cédula del usuario a inactivar"}, status=400)

    try:
        usuario = Usuario.objects.get(cedula=cedula)
    except Usuario.DoesNotExist:
        return Response({"message": "Usuario no encontrado"}, status=404)

    if not usuario.active:
        return Response({"message": "El usuario ya está inactivo"}, status=400)

    usuario.active = False
    usuario.save()

    return Response({"message": f"Usuario con cédula {cedula} ha sido inactivado exitosamente"}, status=200)
