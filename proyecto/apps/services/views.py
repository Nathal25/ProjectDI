#from apps.authentication import models
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ConsultaMedica, ReclamarMedicamentos, Asesoramiento, Usuario
from django.db import transaction, models
from django.db.models import Max
from django.shortcuts import get_object_or_404
from apps.authentication.views import decodificar_jwt, get_datos_usuario
from django.core.cache import cache
SERVICIOS = {
    "consulta": ConsultaMedica,
    "medicamentos": ReclamarMedicamentos,
    "asesoramiento": Asesoramiento,
}

@api_view(['POST'])
def pasar_turno(request):
    # Validar token y rol de asesor
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

    # Obtener el servicio desde el body
    servicio = request.data.get("servicio")
    if not servicio:
        return Response({"error": "Debes indicar el parámetro 'servicio'"}, status=400)

    Modelo = SERVICIOS.get(servicio.lower())
    if not Modelo:
        return Response({"error": "Servicio inválido"}, status=400)

    # Buscar el siguiente turno pendiente (prioritario > general)
    turno = Modelo.objects.filter(estado='Pendiente').order_by(
        models.Case(
            models.When(prioritario__isnull=False, then=0),
            models.When(general__isnull=False, then=1),
            default=2,
        ),
        'prioritario',
        'general'
    ).first()

    if not turno:
        return Response({"error": "No hay turnos pendientes"}, status=404)

    turno.estado = 'Atendido'
    turno.save()
    turno_id = turno.id
    turno.delete()

    # return Response({
    #     "mensaje": f"Turno atendido correctamente",
    #     "turno": {
    #         "id": turno.id,
    #         "prioritario": turno.prioritario,
    #         "general": turno.general,
    #         "estado": turno.estado
    #     }
    # })

    return Response({
        "mensaje": f"Turno con id {turno_id} atendido y eliminado correctamente",
        "turno_id": turno_id
    })

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

@api_view(['POST'])
def cancelar_turno(request):
    # Validar token del usuario
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

    # Obtener el servicio desde el body
    servicio = request.data.get("servicio")
    if not servicio:
        return Response({"error": "Debes indicar el parámetro 'servicio'"}, status=400)

    Modelo = SERVICIOS.get(servicio.lower())
    if not Modelo:
        return Response({"error": "Servicio inválido"}, status=400)

    # Buscar el turno pendiente del usuario en ese servicio
    turno = Modelo.objects.filter(usuario=usuario, estado='Pendiente').first()

    if not turno:
        return Response({"error": "No tienes turnos pendientes en este servicio"}, status=404)

    turno_id = turno.id
    turno.delete()

    return Response({
        "mensaje": f"Turno cancelado correctamente en el servicio '{servicio}'",
        "turno_id": turno_id
    })
