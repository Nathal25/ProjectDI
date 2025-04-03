from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Usuario
from .serializers import UsuarioSerializer

@api_view(['POST'])
def registrar_usuario_api(request):
    serializer = UsuarioSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Registro exitoso"}, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def login_usuario_api(request):
    cedula = request.data.get("cedula")  # verifica si existe la cedula
    if Usuario.objects.filter(cedula=cedula).exists():  # Verifica si ya existe
        return Response({"message": "El usuario ya está registrado"}, status=400)

    serializer = UsuarioSerializer(data=request.data)
    # if serializer.is_valid():
    #     serializer.save()
    return Response({"message": "No está registrado"}, status=201)
    
    #return Response(serializer.errors, status=201)