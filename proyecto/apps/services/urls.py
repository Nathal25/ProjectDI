from .views import solicitud_turnos, pasar_turno, cancelar_turno
from django.urls import path

urlpatterns = [
    path('solicitud', solicitud_turnos, name='solicitud_turnos'),
    path('pasar-turno', pasar_turno, name='pasar_turno'),
    path('cancelar-turno', cancelar_turno, name='cancelar_turno')
]