from .views import solicitud_turnos
from django.urls import path

urlpatterns = [
    path('solicitud', solicitud_turnos, name='solicitud_turnos'),
]