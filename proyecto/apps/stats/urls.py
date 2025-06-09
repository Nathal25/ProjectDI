from .views import (estadisticas_solicitud_servicios, estadisticas_tipos_servicio, estadisticas_servicios_generico,  rendimiento_punto_atencion)
from django.urls import path

urlpatterns = [
    path('servicios-generico', estadisticas_servicios_generico, name='estadisticas_servicios_generico'),
    path('solicitudes-servicios', estadisticas_solicitud_servicios, name='estadisticas_solicitud_servicios'),
    path('tipos-servicio', estadisticas_tipos_servicio, name='estadisticas_tipos_servicio'),
    path('rendimiento-punto-atencion', rendimiento_punto_atencion, name='rendimiento_punto_atencion'),
    # Aquí puedes agregar más rutas para otras estadísticas
]