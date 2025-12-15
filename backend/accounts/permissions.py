from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import UserRole


def has_role(user, code: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    return UserRole.objects.filter(user=user, role__code=code).exists()


def is_admin_user(user) -> bool:
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser or user.is_staff:
        return True

    return has_role(user, "ADMIN")


def is_teacher_user(user) -> bool:
    if not user or not user.is_authenticated:
        return False

    if is_admin_user(user):
        return True

    return has_role(user, "TEACHER")


def is_maintainer_user(user) -> bool:
    if is_admin_user(user):
        return True
    return has_role(user, "MAINTAINER")


class IsAdminUser(BasePermission):
    message = "Admin permission required."

    def has_permission(self, request, view):
        return is_admin_user(getattr(request, "user", None))


class IsAdminOrReadOnly(BasePermission):
    message = "Admin permission required."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if request.method in SAFE_METHODS:
            return bool(user and user.is_authenticated)

        return is_admin_user(user)


class IsTeacherOrAdmin(BasePermission):
    message = "Teacher or admin permission required."

    def has_permission(self, request, view):
        return is_teacher_user(getattr(request, "user", None))


class IsMaintainerOrAdmin(BasePermission):
    message = "Maintainer or admin permission required."

    def has_permission(self, request, view):
        return is_maintainer_user(getattr(request, "user", None))


class IsMaintainerOrAdminOrReadOnly(BasePermission):
    message = "Maintainer or admin permission required."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if request.method in SAFE_METHODS:
            return bool(user and user.is_authenticated)
        return is_maintainer_user(user)
