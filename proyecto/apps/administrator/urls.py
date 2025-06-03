from .views import crear_asesor_admin
from django.urls import path

urlpatterns = [
    path('create_asessor', crear_asesor_admin, name='crear_asesor_admin'),
    
]