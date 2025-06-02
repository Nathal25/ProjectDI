from apps.authentication.models import Usuario
from apps.authentication.serializers import UsuarioSerializer
from apps.authentication.utils import hash_password, validar_token
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.authentication.utils import get_datos_usuario




# Create your views here.

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
        if datos_usuario and datos_usuario.get("rol") == "administrador":
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