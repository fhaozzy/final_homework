from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from accounts.permissions import IsMaintainerOrAdminOrReadOnly
from inventory.models import Equipment, EquipmentStatus, EquipmentStatusLog
from maintenance.models import Maintenance, MaintenanceStatus
from maintenance.serializers import MaintenanceSerializer, MaintenanceWriteSerializer


def _is_maintenance_transition_allowed(from_status: str, to_status: str) -> bool:
    if from_status == to_status:
        return True

    if from_status == MaintenanceStatus.DONE:
        return False

    if from_status == MaintenanceStatus.OPEN:
        return to_status == MaintenanceStatus.IN_PROGRESS

    if from_status == MaintenanceStatus.IN_PROGRESS:
        return to_status == MaintenanceStatus.DONE

    return False


class MaintenanceViewSet(ModelViewSet):
    queryset = Maintenance.objects.select_related("equipment", "assigned_to").all().order_by("-id")
    permission_classes = [IsMaintainerOrAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return MaintenanceWriteSerializer
        return MaintenanceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        status_param = params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        equipment_param = params.get("equipment")
        if equipment_param and equipment_param.isdigit():
            qs = qs.filter(equipment_id=int(equipment_param))

        keyword = params.get("keyword")
        if keyword:
            qs = qs.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword))

        return qs

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        equipment = serializer.validated_data["equipment"]
        equipment = Equipment.objects.select_for_update().get(pk=equipment.pk)

        if equipment.status == EquipmentStatus.DISCARDED:
            raise ValidationError({"equipment": "DISCARDED equipment cannot be maintained."})

        if equipment.status not in {EquipmentStatus.AVAILABLE, EquipmentStatus.MAINTENANCE}:
            raise ValidationError({"equipment": f"Equipment must be AVAILABLE/MAINTENANCE, got {equipment.status}."})

        if equipment.status != EquipmentStatus.MAINTENANCE:
            from_status = equipment.status
            equipment.status = EquipmentStatus.MAINTENANCE
            equipment.save(update_fields=["status", "updated_at"])
            EquipmentStatusLog.objects.create(
                equipment=equipment,
                from_status=from_status,
                to_status=EquipmentStatus.MAINTENANCE,
                changed_by=request.user,
                reason="maintenance_open",
                remark="",
            )

        maintenance = Maintenance.objects.create(
            equipment=equipment,
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get("description", ""),
            status=MaintenanceStatus.OPEN,
            assigned_to=serializer.validated_data.get("assigned_to"),
            cost=serializer.validated_data.get("cost"),
        )

        return Response(MaintenanceSerializer(maintenance).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        maintenance = self.get_queryset().select_for_update().get(pk=kwargs["pk"])
        serializer = self.get_serializer(maintenance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        now = timezone.now()

        new_status = serializer.validated_data.get("status")
        if new_status and not _is_maintenance_transition_allowed(maintenance.status, new_status):
            raise ValidationError({"status": f"Invalid transition: {maintenance.status} -> {new_status}"})

        equipment = Equipment.objects.select_for_update().get(pk=maintenance.equipment_id)

        for key in ["title", "description", "assigned_to", "cost"]:
            if key in serializer.validated_data:
                setattr(maintenance, key, serializer.validated_data[key])

        if new_status and new_status != maintenance.status:
            if equipment.status != EquipmentStatus.MAINTENANCE:
                raise ValidationError({"equipment": f"Equipment must be MAINTENANCE to update status, got {equipment.status}."})

            if new_status == MaintenanceStatus.IN_PROGRESS and not maintenance.started_at:
                maintenance.started_at = now

            if new_status == MaintenanceStatus.DONE:
                if not maintenance.started_at:
                    maintenance.started_at = now
                maintenance.finished_at = now

                from_status = equipment.status
                equipment.status = EquipmentStatus.AVAILABLE
                equipment.save(update_fields=["status", "updated_at"])
                EquipmentStatusLog.objects.create(
                    equipment=equipment,
                    from_status=from_status,
                    to_status=EquipmentStatus.AVAILABLE,
                    changed_by=request.user,
                    reason="maintenance_done",
                    remark=f"maintenance:{maintenance.id}",
                )

            maintenance.status = new_status

        maintenance.updated_at = now
        maintenance.save()

        maintenance = self.get_queryset().get(pk=maintenance.pk)
        return Response(MaintenanceSerializer(maintenance).data, status=status.HTTP_200_OK)

