from .views import registrar_usuario_api, identifier_usuario_api, validar_password_usuario_api, validar_token_api, cambiar_punto_atencion
from django.urls import path

urlpatterns = [
    path('registro', registrar_usuario_api, name='registro_usuario_api'),
    path('login', identifier_usuario_api, name='identifier_usuario_api'),
    path('validar_password', validar_password_usuario_api, name='validar_password_usuario_api'),
    path('validar_token', validar_token_api, name='validar_token_api'),
    path('cambiar_punto_atencion', cambiar_punto_atencion, name='cambiar_punto_atencion_api'),
]