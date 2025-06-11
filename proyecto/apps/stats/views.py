from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from apps.services.models import ConsultaMedica, ReclamarMedicamentos, Asesoramiento
from apps.authentication.models import Usuario
from django.contrib.auth.decorators import login_required
from .permissions import IsAdminRole
from apps.authentication.views import decodificar_jwt

SERVICIOS = {
    'consulta': ConsultaMedica,
    'medicamentos': ReclamarMedicamentos,
    'asesoramiento': Asesoramiento,
}


# 1. Estadísticas de servicios genéricos
# Esta vista permite obtener estadísticas de un servicio específico (consulta, medicamentos, asesoramiento)
@permission_classes([IsAdminRole])
@api_view(['GET', 'POST'])
def estadisticas_servicios_generico(request):
    usuario_admin = get_punto_atencion_admin(request)
    if IsAdminRole().has_permission(request, None) is False:
        return Response({"error": "No tienes permiso para acceder a esta vista"}, status=403)
    
    punto_atencion = PuntoAtencionPermission
    filtro = {'usuario__puntoAtencion': punto_atencion}

    # Soporta GET (params) o POST (body JSON)
    if request.method == 'GET':
        servicio = request.query_params.get('servicio')
        tipo_turno = request.query_params.get('tipo')
    else:
        servicio = request.data.get('servicio')
        tipo_turno = request.data.get('tipo')

    if not servicio:
        return Response({'error': 'Debe indicar el servicio.'}, status=400)
    modelo = SERVICIOS.get(servicio.lower())
    if not modelo:
        return Response({'error': 'Servicio inválido.'}, status=400)

    respuesta = {}
    # Validar punto de atención
    filtro = {'usuario__puntoAtencion': punto_atencion}
    if tipo_turno == 'prioritario':
        total_prioritario = modelo.objects.filter(prioritario__isnull=False, **filtro).count()
        respuesta['prioritario'] = {
            'servicio': servicio,
            'total': total_prioritario,
            'porcentaje': 100.0
        }
    elif tipo_turno == 'general':
        total_general = modelo.objects.filter(general__isnull=False, **filtro).count()
        respuesta['general'] = {
            'servicio': servicio,
            'total': total_general,
            'porcentaje': 100.0
        }
    else:
        total_prioritario = modelo.objects.filter(prioritario__isnull=False, **filtro).count()
        total_general = modelo.objects.filter(general__isnull=False, **filtro).count()
        total = total_prioritario + total_general
        respuesta = {
            'servicio': servicio,
            'prioritario': {
                'total': total_prioritario,
                'porcentaje': round((total_prioritario / total * 100), 2) if total > 0 else 0
            },
            'general': {
                'total': total_general,
                'porcentaje': round((total_general / total * 100), 2) if total > 0 else 0
            }
        }
    return Response(respuesta)

# 2. Estadísticas de solicitudes de servicios
# Esta vista devuelve estadísticas de las solicitudes de servicios por usuario.
@permission_classes([IsAdminRole])
@api_view(['GET'])
def estadisticas_solicitud_servicios(request):
    usuario_admin = get_punto_atencion_admin(request)

    if IsAdminRole().has_permission(request, None) is False:
        return Response({"error": "No tienes permiso para acceder a esta vista"}, status=403)
    
    punto_atencion = usuario_admin.puntoAtencion

    usuarios = Usuario.objects.filter(puntoAtencion=punto_atencion).annotate(
        total_solicitudes=Count('consultamedica_turnos') + 
        Count('reclamarmedicamentos_turnos') + 
        Count('asesoramiento_turnos')
        ).filter(total_solicitudes__gt=0)
    
    # Calcular total general
    total_general = sum(usuario.total_solicitudes for usuario in usuarios)
    
    # Formatear respuesta
    data = [{
        "usuario_id": usuario.id,
        "nombre": usuario.nombre,
        "solicitudes": usuario.total_solicitudes,
        "porcentaje": round((usuario.total_solicitudes / total_general * 100), 2) if total_general > 0 else 0
    } for usuario in usuarios]
    
    return Response(data)

# 3. Estadísticas de tipos de servicio
# Esta vista devuelve estadísticas de los tipos de servicio (prioritario y general) 
# para cada modelo de servicio.
# Se agregan los totales y porcentajes de cada tipo de servicio.
@permission_classes([IsAdminRole])
@api_view(['GET'])
def estadisticas_tipos_servicio(request):
    usuario_admin = get_punto_atencion_admin(request)
    if IsAdminRole().has_permission(request, None) is False:
        return Response({"error": "No tienes permiso para acceder a esta vista"}, status=403)
    punto_atencion = usuario_admin.puntoAtencion
    # Inicializar contadores
    total_prioritario = 0
    total_general = 0
    
    # Calcular para cada modelo de servicio
    for modelo in [ConsultaMedica, ReclamarMedicamentos, Asesoramiento]:
        stats = modelo.objects.filter(punto_atencion=punto_atencion).aggregate(
            prio=Count('id', filter=Q(prioritario__isnull=False)),
            gen=Count('id', filter=Q(general__isnull=False))
        )
        total_prioritario += stats['prio']
        total_general += stats['gen']
    
    total = total_prioritario + total_general
    
    return Response({
        "prioritario": {
            "total": total_prioritario,
            "porcentaje": round((total_prioritario / total * 100), 2) if total > 0 else 0
        },
        "general": {
            "total": total_general,
            "porcentaje": round((total_general / total * 100), 2) if total > 0 else 0
        }
    })

# 4. Rendimiento general del punto de atención
# Esta vista devuelve estadísticas del rendimiento de cada punto de atención,
# incluyendo el total de turnos, turnos atendidos, y la cantidad de turnos prioritarios y generales.
@permission_classes([IsAdminRole])
@api_view(['GET'])
def rendimiento_punto_atencion(request):
    if IsAdminRole().has_permission(request, None) is False:
        return Response({"error": "No tienes permiso para acceder a esta vista"}, status=403)   
    
    # Obtener todos los puntos de atención únicos
    puntos = Usuario.objects.values_list('puntoAtencion', flat=True).distinct()
    resultado = []
    for punto in puntos:
        # Total de turnos en el punto
        total = (
            ConsultaMedica.objects.filter(usuario__puntoAtencion=punto).count() +
            ReclamarMedicamentos.objects.filter(usuario__puntoAtencion=punto).count() +
            Asesoramiento.objects.filter(usuario__puntoAtencion=punto).count()
        )
        # Total de turnos atendidos en el punto
        atendidos = (
            ConsultaMedica.objects.filter(usuario__puntoAtencion=punto, estado='Atendido').count() +
            ReclamarMedicamentos.objects.filter(usuario__puntoAtencion=punto, estado='Atendido').count() +
            Asesoramiento.objects.filter(usuario__puntoAtencion=punto, estado='Atendido').count()
        )
        porcentaje = round((atendidos / total) * 100, 2) if total else 0
        resultado.append({
            "punto_atencion": punto,
            "total_turnos": total,
            "total_atendidos": atendidos,
            "porcentaje_atendidos": porcentaje
        })
    return Response(resultado)

#Función auxiliar para obtener el punto de atención del usuario administrador
def get_punto_atencion_admin(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    payload = decodificar_jwt(token)
    if not payload:
        return None
    usuario_id = payload.get("usuario_id")
    try:
        return Usuario.objects.get(pk=usuario_id)
    except Usuario.DoesNotExist:
        return None