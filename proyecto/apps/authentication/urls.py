from .views import registrar_usuario_api, login_usuario_api
from django.urls import path

urlpatterns = [
    path('registro', registrar_usuario_api, name='registro_usuario_api'),
    path('login', login_usuario_api, name='login_usuario_api'),
]