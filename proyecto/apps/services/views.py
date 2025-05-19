#from apps.authentication import models
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ConsultaMedica, ReclamarMedicamentos, Asesoramiento, Usuario
from django.db import transaction, models
from django.db.models import Max
from django.shortcuts import get_object_or_404
from apps.authentication.views import decodificar_jwt, get_datos_usuario
SERVICIOS = {
    "consulta": ConsultaMedica,
    "medicamentos": ReclamarMedicamentos,
    "asesoramiento": Asesoramiento,
}

@api_view(['POST'])
def pasar_turno(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({"error": "Token no proporcionado o mal formado"}, status=400)

    token = auth_header.split(' ')[1]
    payload = decodificar_jwt(token)

    if not payload:
        return Response({"error": "Token inválido o expirado"}, status=401)

    usuario_id = payload.get("usuario_id")
    if not usuario_id:
        return Response({"error": "Token inválido"}, status=401)

    try:
        usuario = Usuario.objects.get(pk=usuario_id)
    except Usuario.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=404)

    if usuario.rol != 'asesor':
        return Response({"error": "No tienes permiso para modificar turnos"}, status=403)

    turno_id = request.data.get("turno_id")
    servicio = request.data.get("service")

    if not turno_id or not servicio:
        return Response({"error": "turno_id y service son requeridos"}, status=400)

    Modelo = SERVICIOS.get(servicio.lower())
    if not Modelo:
        return Response({"error": "Servicio inválido"}, status=400)

    try:
        turno = Modelo.objects.get(pk=turno_id)
    except Modelo.DoesNotExist:
        return Response({"error": "Turno no encontrado"}, status=404)

    if turno.estado == 'Pendiente':
        turno.estado = 'Atendido'
    elif turno.estado == 'Atendido':
        turno.estado = 'Pasado'
    else:
        return Response({"error": f"No se puede avanzar el estado desde {turno.estado}"}, status=400)

    turno.save()
    return Response({"status": f"Turno actualizado a {turno.estado.lower()}"})

@api_view(['GET'])
def solicitud_turnos(request):
    id_usuario = request.query_params.get("id")
    servicio = request.query_params.get("service")

    if not id_usuario or not servicio:
        return Response({"error": "Faltan parámetros"}, status=400)

    try:
        usuario = Usuario.objects.get(pk=id_usuario)
    except Usuario.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=404)

    modelo_servicio = SERVICIOS.get(servicio.lower())
    if not modelo_servicio:
        return Response({"error": "Servicio inválido"}, status=400)

    try:
        with transaction.atomic():
            punto = usuario.puntoAtencion
            if usuario.discapacidad:
                ultimo = modelo_servicio.objects.filter(usuario__puntoAtencion=punto).aggregate(max_p=models.Max("prioritario"))["max_p"] or 0
                turno = modelo_servicio.objects.create(prioritario=ultimo + 1, general=None, usuario=usuario)
                return Response({"turno_prioritario": turno.prioritario}, status=201)
            else:
                ultimo = modelo_servicio.objects.filter(usuario__puntoAtencion=punto).aggregate(max_g=models.Max("general"))["max_g"] or 0
                turno = modelo_servicio.objects.create(prioritario=None, general=ultimo + 1, usuario=usuario)
                return Response({"turno_general": turno.general}, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

