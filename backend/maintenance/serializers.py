from rest_framework import serializers

from maintenance.models import Maintenance


class MaintenanceSerializer(serializers.ModelSerializer):
    equipment_code = serializers.CharField(source="equipment.code", read_only=True)
    equipment_name = serializers.CharField(source="equipment.name", read_only=True)
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)

    class Meta:
        model = Maintenance
        fields = [
            "id",
            "equipment_id",
            "equipment_code",
            "equipment_name",
            "title",
            "description",
            "status",
            "assigned_to",
            "assigned_to_username",
            "cost",
            "started_at",
            "finished_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MaintenanceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maintenance
        fields = [
            "id",
            "equipment",
            "title",
            "description",
            "status",
            "assigned_to",
            "cost",
        ]
        read_only_fields = ["id"]

