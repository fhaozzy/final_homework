from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import UserRole


class IsAdminOrReadOnly(BasePermission):
    message = "Admin permission required."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if request.method in SAFE_METHODS:
            return bool(user and user.is_authenticated)

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser or user.is_staff:
            return True

        return UserRole.objects.filter(user=user, role__code="ADMIN").exists()
