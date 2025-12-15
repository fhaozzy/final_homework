from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from accounts.permissions import IsAdminOrReadOnly
from inventory.models import Equipment, EquipmentCategory, EquipmentStatus, EquipmentStatusLog
from inventory.serializers import (
    EquipmentCategorySerializer,
    EquipmentSerializer,
    EquipmentStatusChangeSerializer,
    EquipmentStatusLogSerializer,
)


def _is_transition_allowed(from_status: str, to_status: str) -> bool:
    if from_status == to_status:
        return False

    if from_status == EquipmentStatus.DISCARDED:
        return False

    if to_status in {EquipmentStatus.MAINTENANCE, EquipmentStatus.DISCARDED}:
        return True

    if from_status == EquipmentStatus.MAINTENANCE:
        return to_status == EquipmentStatus.AVAILABLE

    if from_status == EquipmentStatus.AVAILABLE:
        return to_status == EquipmentStatus.RESERVED

    if from_status == EquipmentStatus.RESERVED:
        return to_status in {EquipmentStatus.OUT, EquipmentStatus.AVAILABLE}

    if from_status == EquipmentStatus.OUT:
        return to_status == EquipmentStatus.RETURN_PENDING

    if from_status == EquipmentStatus.RETURN_PENDING:
        return to_status == EquipmentStatus.AVAILABLE

    return False


class EquipmentCategoryViewSet(ModelViewSet):
    queryset = EquipmentCategory.objects.all().order_by("-id")
    serializer_class = EquipmentCategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class EquipmentViewSet(ModelViewSet):
    serializer_class = EquipmentSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Equipment.objects.select_related("category").all().order_by("-id")
        params = self.request.query_params

        status_param = params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        category_param = params.get("category")
        if category_param:
            if category_param.isdigit():
                queryset = queryset.filter(category_id=int(category_param))
            else:
                queryset = queryset.filter(category__code=category_param)

        keyword = params.get("keyword")
        if keyword:
            queryset = queryset.filter(Q(code__icontains=keyword) | Q(name__icontains=keyword))

        return queryset

    @action(detail=True, methods=["post"], url_path="status")
    @transaction.atomic
    def change_status(self, request, pk=None):
        equipment = Equipment.objects.select_for_update().get(pk=pk)
        serializer = EquipmentStatusChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from_status = equipment.status
        to_status = serializer.validated_data["to_status"]
        reason = serializer.validated_data.get("reason", "")
        remark = serializer.validated_data.get("remark", "")

        if not _is_transition_allowed(from_status=from_status, to_status=to_status):
            raise ValidationError({"to_status": f"Invalid transition: {from_status} -> {to_status}"})

        equipment.status = to_status
        equipment.save(update_fields=["status", "updated_at"])

        EquipmentStatusLog.objects.create(
            equipment=equipment,
            from_status=from_status,
            to_status=to_status,
            changed_by=request.user,
            reason=reason,
            remark=remark,
        )

        return Response(EquipmentSerializer(equipment).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="logs")
    def logs(self, request, pk=None):
        equipment = self.get_object()
        logs_qs = equipment.status_logs.select_related("changed_by").order_by("-created_at", "-id")
        return Response(EquipmentStatusLogSerializer(logs_qs, many=True).data, status=status.HTTP_200_OK)
