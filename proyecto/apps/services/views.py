#from apps.authentication import models
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ConsultaMedica, ReclamarMedicamentos, Asesoramiento, Usuario
from apps.authentication.utils import validar_token
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

"""
pasar_turno(request)
-------------------
Endpoint para avanzar el turno en un servicio específico. Solo los usuarios con rol de 'asesor' pueden acceder a esta funcionalidad.
Método: POST
Permite que un asesor pase el turno actual en estado 'Atendido' a 'Pasado' y atienda el siguiente turno pendiente (priorizando los turnos prioritarios sobre los generales) en el servicio indicado.
Parámetros en el body (JSON):
- servicio (str): Nombre del servicio sobre el cual se desea pasar el turno. Debe ser uno de: 'consulta', 'medicamentos', 'asesoramiento'.
Requiere autenticación mediante token JWT.
Flujo:
1. Valida el token y el rol del usuario.
2. Cambia el estado del turno actual 'Atendido' a 'Pasado' (si existe).
3. Busca el siguiente turno pendiente ('Pendiente'), priorizando los turnos prioritarios.
4. Cambia el estado de ese turno a 'Atendido'.
5. Devuelve información del turno actualizado.
Respuestas:
- 200 OK: Retorna mensaje de éxito, id, tipo y número del turno atendido.
- 400 Bad Request: Si falta el parámetro 'servicio' o el servicio es inválido.
- 401 Unauthorized: Si el token es inválido o expirado, o si el usuario no es asesor.
- 403 Forbidden: Si el usuario no tiene permisos para modificar turnos.
- 404 Not Found: Si el usuario no existe o no hay turnos pendientes.
Ejemplo de respuesta exitosa:
{
    "mensaje": "Turno prioritario 5 actualizado a 'Atendido'",
    "turno_id": 12,
    "tipo": "prioritario",
    "numero": 5
}
"""
@api_view(['POST'])
def pasar_turno(request):
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
    
""""
solicitud_turnos(request)
-------------------------
Endpoint para solicitar un turno en un servicio específico. El usuario debe estar autenticado mediante un token JWT.
Método: GET
Permite a un usuario solicitar un turno en uno de los servicios disponibles ('consulta', 'medicamentos', 'asesoramiento'). Si el usuario ya tiene un turno pendiente en ese servicio, se le informa el turno existente. Si no, se le asigna un nuevo turno, priorizando a usuarios con discapacidad.
Parámetros de consulta (query params):
- service (str): Nombre del servicio para el cual se solicita el turno. Debe ser uno de: 'consulta', 'medicamentos', 'asesoramiento'.
1. Valida el token y obtiene el usuario.
2. Verifica si el usuario ya tiene un turno pendiente en el servicio solicitado.
    - Si ya tiene un turno pendiente, retorna la información de ese turno.
    - Si no tiene un turno pendiente:
      a. Si el usuario tiene discapacidad, se le asigna un turno prioritario.
      b. Si no, se le asigna un turno general.
3. Devuelve la información del turno asignado o existente.
- 200 OK: Si el usuario ya tiene un turno pendiente, retorna la información del turno.
                "id": 3,
                "numero": 2
- 201 Created: Si se asigna un nuevo turno, retorna el número del turno asignado.
          "turno_prioritario": 3
     o
          "turno_general": 5
- 400 Bad Request: Si falta el parámetro 'service' o el servicio es inválido.
          "error": "Faltan parámetros"
     o
          "error": "Servicio inválido"
- 401 Unauthorized: Si el token es inválido o expirado.
          "error": "Token inválido o expirado"
- 404 Not Found: Si el usuario no existe.
          "error": "Usuario no encontrado"
- 500 Internal Server Error: Si ocurre un error inesperado.
          "error": "Descripción del error"
"""
@api_view(['GET'])
def solicitud_turnos(request):
    payload = validar_token(request)
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
"""
cancelar_turno(request)
-------------------
Endpoint para cancelar un turno pendiente en un servicio específico. Solo los usuarios con token válido pueden acceder a esta funcionalidad.
Método: POST
Permite a un usuario cancelar un turno pendiente en uno de los servicios disponibles ('consulta', 'medicamentos', 'asesoramiento').
Parámetros en el body (JSON):
- servicio (str): Nombre del servicio en el cual se desea cancelar el turno. Debe ser uno de: 'consulta', 'medicamentos', 'asesoramiento'.
Requiere autenticación mediante token JWT.
Flujo:
1. Valida el token del usuario.
2. Verifica si el usuario tiene un turno pendiente en el servicio indicado.
3. Si existe un turno pendiente, lo elimina.
4. Devuelve un mensaje de éxito y el ID del turno cancelado.
Respuestas:
- 200 OK: Retorna mensaje de éxito y el ID del turno cancelado.
- 400 Bad Request: Si falta el parámetro 'servicio' o el servicio es
inválido.
- 401 Unauthorized: Si el token es inválido o expirado.
- 404 Not Found: Si el usuario no existe o no tiene turnos pendientes en el
servicio indicado.
Ejemplo de respuesta exitosa:
{
    "mensaje": "Turno cancelado correctamente en el servicio 'consulta'",
    "turno_id": 12
}
"""
@api_view(['POST'])
def cancelar_turno(request):
   #validar token
    payload = validar_token(request)

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
"""
visualizar_turnos(request)
------------------- 
Endpoint para visualizar el turno actual y los últimos turnos pasados en un servicio específico.
Método: GET
Permite a un usuario ver el turno actual (en estado 'Atendido') y los últimos 4 turnos pasados (en estado 'Pasado') de un servicio determinado.
Parámetros de consulta (query params):
- servicio (str): Nombre del servicio para el cual se desea ver los turnos. Debe ser uno de: 'consulta', 'medicamentos', 'asesoramiento'.
Flujo:
1. Valida el token del usuario.
2. Verifica si el servicio es válido.
3. Obtiene el turno actual (en estado 'Atendido') y los últimos 4 turnos pasados (en estado 'Pasado') del servicio indicado.
4. Formatea los resultados para incluir el ID, tipo (prioritario o general) y número del turno.
Respuestas:
- 200 OK: Retorna el turno actual y los últimos 4 turnos pasados en el servicio solicitado.
- 400 Bad Request: Si falta el parámetro 'servicio' o el servicio es inválido.
- 401 Unauthorized: Si el token es inválido o expirado.
- 404 Not Found: Si el servicio no existe.
Ejemplo de respuesta exitosa:
{
    "turno_actual": {
        "id": 12,
        "tipo": "prioritario",
        "numero": 5
    },
    "ultimos_turnos": [
        {"id": 10, "tipo": "general", "numero": 3},
        {"id": 9, "tipo": "prioritario", "numero": 2},
        {"id": 8, "tipo": "general", "numero": 1},
        {"id": 7, "tipo": "prioritario", "numero": 4}
    ]
}
"""
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
"""
turno_pendiente(request)
-------------------
Endpoint para obtener los turnos pendientes de un usuario en todos los servicios.
Método: GET
Permite a un usuario ver los turnos pendientes que tiene en los diferentes servicios disponibles ('consulta', 'medicamentos', 'asesoramiento').
Requiere autenticación mediante token JWT.
Flujo:
1. Valida el token del usuario.
2. Verifica si el usuario existe.
3. Recorre todos los servicios y busca turnos pendientes del usuario.
4. Devuelve un resumen de los turnos pendientes, indicando el ID, número y tipo (prioritario o general) de cada turno.
Respuestas:
- 200 OK: Retorna un resumen de los turnos pendientes del usuario en los diferentes servicios.
- 401 Unauthorized: Si el token es inválido o expirado.
- 404 Not Found: Si el usuario no existe o no tiene turnos pendientes en ningún servicio.
Ejemplo de respuesta exitosa:
{
    "mensaje": "Usuario con turnos pendientes en los siguientes servicios: ",
    "turnos": {
        "consulta": {
            "id": 12,
            "turno": 5,
            "tipo": "prioritario"
        },
        "medicamentos": {
            "id": 15,
            "turno": 3,
            "tipo": "general"
        }
    }
}
"""
@api_view(['GET'])
def turno_pendiente(request):
    # Validar token del usuario
    payload = validar_token(request)

    if not payload:
        return Response({"error": "Token inválido o expirado"}, status=401)

    usuario_id = payload.get("usuario_id")
    if not usuario_id:
        return Response({"error": "Token inválido"}, status=401)

    try:
        usuario = Usuario.objects.get(pk=usuario_id)
    except Usuario.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=404)

     # Recorrer todos los modelos de servicios
    turnos_pendientes = {}
    for nombre_servicio, Modelo in SERVICIOS.items():
        turno = Modelo.objects.filter(usuario=usuario, estado='Pendiente').first()
        if turno:
            tipo = "prioritario" if turno.prioritario is not None else "general"
            numero = turno.prioritario if tipo == "prioritario" else turno.general
            turnos_pendientes[nombre_servicio] = {
                "id": turno.id,
                "turno": numero,
                "tipo": tipo
            }

    if not turnos_pendientes:
        return Response({"mensaje": "El usuario no tiene turnos pendientes en ningún servicio."})

    return Response({
        "mensaje": f"Usuario con turnos pendientes en los siguientes servicios: ",
        "turnos": turnos_pendientes
    })