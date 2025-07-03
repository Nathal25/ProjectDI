from .views import solicitud_turnos, pasar_turno, cancelar_turno, visualizar_turnos, turno_pendiente
from django.urls import path

urlpatterns = [
    path('solicitud', solicitud_turnos, name='solicitud_turnos'),
    path('pasar-turno', pasar_turno, name='pasar_turno'),
    path('cancelar-turno', cancelar_turno, name='cancelar_turno'),
    path('visualizar-turno', visualizar_turnos, name='visualizar-turno'),
    path('turno-pendiente', turno_pendiente, name='turno-pendiente')
]