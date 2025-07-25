from .views import crear_asesor_admin, subir_anuncio, traer_anuncios, eliminar_usuario,borrar_anuncio
from django.urls import path

urlpatterns = [
    path('create_asessor', crear_asesor_admin, name='crear_asesor_admin'),
    path('subir_anuncio', subir_anuncio, name='subir_anuncio'),
    path('traer_anuncios', traer_anuncios , name='traer_anuncios'),
    path('eliminar_usuario', eliminar_usuario, name='eliminar_usuario'),
    path('borrar_anuncio', borrar_anuncio, name='borrar_anuncio'),
]