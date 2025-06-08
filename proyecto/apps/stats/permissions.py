from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        print("User:", request.user)
        print("Is authenticated:", request.user.is_authenticated)
        print("Rol:", getattr(request.user, 'rol', None))
        return (
            request.user.is_authenticated and
            getattr(request.user, 'rol', None) == 'admin'
        )

