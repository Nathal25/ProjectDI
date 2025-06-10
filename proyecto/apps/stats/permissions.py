from rest_framework import permissions
from apps.authentication.views import decodificar_jwt
from apps.authentication.models import Usuario

class IsAdminRole(permissions.BasePermission):
    message = "No tienes permiso para acceder a este recurso."

    def has_permission(self, request, view):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            self.message = "Token no proporcionado o mal formado"
            return False

        token = auth_header.split(' ')[1]
        payload = decodificar_jwt(token)

        if not payload:
            self.message = "Token inválido o expirado"
            return False

        usuario_id = payload.get("usuario_id")
        if not usuario_id:
            self.message = "Token inválido"
            return False

        try:
            usuario = Usuario.objects.get(pk=usuario_id)
        except Usuario.DoesNotExist:
            self.message = "Usuario no encontrado"
            return False

        if usuario.rol != 'admin':
            self.message = "No tienes permiso para acceder a las estadísticas"
            return False

        return True
