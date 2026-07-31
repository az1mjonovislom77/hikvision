from django.contrib.auth import get_user_model
from rest_framework.permissions import SAFE_METHODS, BasePermission

User = get_user_model()


def is_admin(user):
    return bool(user and user.is_authenticated and (user.is_staff or user.role == User.UserRoles.SUPERADMIN))


class IsAdminOrSuperadmin(BasePermission):
    message = "Ruxsat yo'q"

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsAdminOrReadOnly(BasePermission):
    message = "Ruxsat yo'q"

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return is_admin(request.user)
