from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from accounts.models import Role, UserRole
from accounts.permissions import IsAdminUser
from accounts.serializers import (
    RoleSerializer,
    UserRoleSerializer,
    UserRoleWriteSerializer,
    UserSerializer,
    UserWriteSerializer,
)

User = get_user_model()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("id")
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return UserWriteSerializer
        return UserSerializer

    @action(detail=True, methods=["patch"], url_path="activate")
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class RoleViewSet(ModelViewSet):
    queryset = Role.objects.all().order_by("id")
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]


class UserRoleViewSet(ModelViewSet):
    queryset = UserRole.objects.select_related("user", "role").all().order_by("id")
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return UserRoleWriteSerializer
        return UserRoleSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            instance = serializer.save()
        except IntegrityError as exc:
            raise ValidationError({"detail": "User already has this role."}) from exc
        return Response(UserRoleSerializer(instance).data, status=status.HTTP_201_CREATED)

