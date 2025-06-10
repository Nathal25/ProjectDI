#from apps.authentication import models
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ConsultaMedica, ReclamarMedicamentos, Asesoramiento, Usuario
from django.db import transaction, models
from django.db.models import Max
from django.shortcuts import get_object_or_404
from apps.authentication.views import decodificar_jwt, get_datos_usuario
from django.core.cache import cache

#tipos de servicios
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
        return Response({"error": "Usuario no encontrado en base de datos"}, status=404)

    if usuario.rol != 'asesor':
        return Response({"error": "No tienes permiso para modificar turnos"}, status=403)

    # Obtener el servicio desde el body
    servicio = request.data.get("servicio")
    if not servicio:
        return Response({"error": "Debes indicar el parámetro 'servicio'"}, status=400)

    Modelo = SERVICIOS.get(servicio.lower())
    if not Modelo:
        return Response({"error": "Servicio inválido"}, status=400)

    # 1. Si hay un turno en estado 'Atendido', pasarlo a 'Pasado'
    turno_atendido = Modelo.objects.filter(estado='Atendido').first()
    if turno_atendido:
        turno_atendido.estado = 'Pasado'
        turno_atendido.save()
    
    # 2. Buscar siguiente turno 'Pendiente' (prioritario > general)
    turno_pendiente = Modelo.objects.filter(estado='Pendiente').order_by(
        models.Case(
            models.When(prioritario__isnull=False, then=0),
            models.When(general__isnull=False, then=1),
            default=2,
        ),
        'prioritario',
        'general'
    ).first()

    if not turno_pendiente:
        return Response({"error": "No hay turnos pendientes"}, status=404)
    
    # 3. Cambiar ese turno a 'Atendido'
    turno_pendiente.estado = 'Atendido'
    turno_pendiente.save()

    tipo = "prioritario" if turno_pendiente.prioritario is not None else "general"
    numero = turno_pendiente.prioritario if tipo == "prioritario" else turno_pendiente.general

    return Response({
        "mensaje": f"Turno {tipo} {numero} actualizado a 'Atendido'",
        "turno_id": turno_pendiente.id,
        "tipo": tipo,
        "numero": numero
    })
    

@api_view(['GET'])
def solicitud_turnos(request):
    #validar el ingreso como paciente 
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
    

    servicio = request.query_params.get("service")

    if not servicio:
        return Response({"error": "Faltan parámetros"}, status=400)

    modelo_servicio = SERVICIOS.get(servicio.lower())
    if not modelo_servicio:
        return Response({"error": "Servicio inválido"}, status=400)

    try:
        # Verificar si ya tiene un turno pendiente en ese servicio
        turno_existente = modelo_servicio.objects.filter(usuario=usuario, estado='Pendiente').first()
        if turno_existente:
            tipo = "prioritario" if turno_existente.prioritario is not None else "general"
            numero = turno_existente.prioritario if tipo == "prioritario" else turno_existente.general
            return Response({
                "mensaje": "Ya tienes un turno pendiente",
                "turno": {
                    "id": turno_existente.id,
                    "tipo": tipo,
                    "numero": numero
                }
            }, status=200)
        
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

@api_view(['GET'])
def visualizar_turnos(request):
    servicio = request.query_params.get("servicio")
    if not servicio:
        return Response({"error": "Debes enviar el parámetro 'servicio'"}, status=400)

    Modelo = SERVICIOS.get(servicio.lower())
    if not Modelo:
        return Response({"error": "Servicio inválido"}, status=400)

    # Turno actual
    turno_actual = Modelo.objects.filter(estado='Atendido').first()

    # Turnos pasados (últimos 4)
    turnos_pasados = Modelo.objects.filter(estado='Pasado').order_by('-id')[:4]

    # Formatear resultados
    def formatear_turno(turno):
        if turno is None:
            return None
        tipo = "prioritario" if turno.prioritario is not None else "general"
        numero = turno.prioritario if tipo == "prioritario" else turno.general
        return {
            "id": turno.id,
            "tipo": tipo,
            "numero": numero
        }

    return Response({
        "turno_actual": formatear_turno(turno_actual),
        "ultimos_turnos": [formatear_turno(t) for t in turnos_pasados]
    })