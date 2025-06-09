from rest_framework import permissions
from apps.authentication.views import decodificar_jwt, get_datos_usuario

"""
Permiso personalizado para verificar si el usuario autenticado tiene el rol de administrador.
La clase `IsAdminRole` extiende `permissions.BasePermission` de Django REST Framework y sobreescribe el método `has_permission`. Este método valida la presencia y formato del token JWT en la cabecera de autorización, decodifica el token para obtener el ID del usuario, verifica que el usuario exista y finalmente comprueba que el usuario tenga el rol de 'admin'. Si alguna de estas validaciones falla, retorna una respuesta de error correspondiente; de lo contrario, permite el acceso a la vista protegida.
Uso típico: aplicar esta clase como permiso en vistas o viewsets para restringir el acceso únicamente a usuarios administradores.
"""

class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({"error": "Token no proporcionado o mal formado"}, status=400)

        token = auth_header.split(' ')[1]
        payload = decodificar_jwt(token)

        if not payload:
            return Response({"error": "Token inválido o expirado"}, status=401)

        usuario_id = payload.get("usuario_id")
        if not usuario_id:
            return Response({"error": "Token inválido"}, status=401)

        try:
            usuario = Usuario.objects.get(pk=usuario_id)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

        if usuario.rol != 'admin':
            return Response({"error": "No tienes permiso para modificar turnos"}, status=403)

