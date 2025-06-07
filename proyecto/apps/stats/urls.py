from .views import (estadisticas_solicitud_servicios, estadisticas_tipos_servicio, estadisticas_consulta_medica, estadisticas_reclamar_medicamentos, estadisticas_asesoramiento, rendimiento_punto_atencion)
from django.urls import path

urlpatterns = [
    path('solicitudes-servicios', estadisticas_solicitud_servicios, name='estadisticas_solicitud_servicios'),
    path('tipos-servicio', estadisticas_tipos_servicio, name='estadisticas_tipos_servicio'),
    path('consultas-medicas', estadisticas_consulta_medica, name='estadisticas_consultas_medicas'),
    path('reclamos-medicamentos', estadisticas_reclamar_medicamentos, name='estadisticas_reclamos_medicamentos'),   
    path('asesoramientos', estadisticas_asesoramiento, name='estadisticas_asesoramiento'),
    path('rendimiento-punto-atencion', rendimiento_punto_atencion, name='rendimiento_punto_atencion'),
    # Aquí puedes agregar más rutas para otras estadísticas
]