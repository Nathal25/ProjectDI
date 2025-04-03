from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Usuario
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
        serializer.save()
        return Response({"message": "Registro exitoso"}, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def login_usuario_api(request):
    cedula = request.data.get("cedula")  # verifica si existe la cedula
    usuario = Usuario.objects.filter(cedula=cedula)
    usuarios_json = serialize('json', usuario)
    if Usuario.objects.filter(cedula=cedula).exists():  # Verifica si ya existe
         # Serializar el QuerySet a JSON
        usuarios_json = serialize('json', usuario)
        # Convertir la cadena JSON en un objeto Python
        usuarios_data = json.loads(usuarios_json)

        fields_list = [item['fields'] for item in usuarios_data]
        # Retornar el objeto JSON
        return Response(fields_list, status=200)

    return Response({"message": "Usuario no esta regristrado"}, status=201)

# @api_view(['POST'])
# def login_usuario_api(request):
#     cedula = request.data.get("cedula")  # verifica si existe la cedula
#     usuario = Usuario.objects.filter(cedula=cedula)

#     # Serializar el QuerySet a JSON
#     usuarios_json = serialize('json', usuario)
#     # Convertir la cadena JSON en un objeto Python
#     usuarios_data = json.loads(usuarios_json)

#     fields_list = [item['fields'] for item in usuarios_data]
#     # Retornar el objeto JSON
#     return Response(fields_list, status=200)