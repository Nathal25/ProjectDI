#from apps.authentication import models
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ConsultaMedica, ReclamarMedicamentos, Asesoramiento, Usuario
from django.db import transaction, models
from django.db.models import Max


SERVICIOS = {
    "consulta": ConsultaMedica,
    "medicamentos": ReclamarMedicamentos,
    "asesoramiento": Asesoramiento,
}
 
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

