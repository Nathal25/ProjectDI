from .views import registrar_usuario_api, validar_password_usuario_api, validar_token_api, cambiar_punto_atencion, verificar_totp
from django.urls import path

urlpatterns = [
    path('registro', registrar_usuario_api, name='registro_usuario_api'),
    path('verify', verificar_totp, name='verificar_totp_api'),
    path('login', validar_password_usuario_api, name='validar_password_usuario_api'),
    path('validar_token', validar_token_api, name='validar_token_api'),
    path('cambiar_punto_atencion', cambiar_punto_atencion, name='cambiar_punto_atencion_api')
]