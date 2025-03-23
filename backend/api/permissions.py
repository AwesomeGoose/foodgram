from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import View


class IsAuthorPermission(permissions.IsAuthenticatedOrReadOnly):
    def has_object_permission(self,
                              request: Request,
                              view: View,
                              obj: object) -> bool:
        """Проверка разрешений для объекта"""
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
