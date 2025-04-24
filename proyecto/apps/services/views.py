from django.shortcuts import render
from rest_framework.decorators import api_view
from apps.authentication.utils import get_datos_usuario
from rest_framework.response import Response

@api_view(['GET'])  # Cambiamos a GET porque los tokens no se mandan por POST
def solicitud_turnos(request):
    id = request.data.get("id")
    service = request.data.get("service")

    discapacidad = get_datos_usuario(id)["discapacidad"]

    if discapacidad != None:
        return Response(discapacidad, status=201)
    return Response({"mensaje": "Usuario sin discapacidad"})

@api_view(['POST'])
def embarazo(request):
    id = request.data.get("id")
    