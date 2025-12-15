from rest_framework import serializers

from inventory.models import Equipment, EquipmentCategory, EquipmentStatus, EquipmentStatusLog


class EquipmentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentCategory
        fields = ["id", "code", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class EquipmentSerializer(serializers.ModelSerializer):
    category = EquipmentCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category", queryset=EquipmentCategory.objects.all(), write_only=True
    )

    class Meta:
        model = Equipment
        fields = [
            "id",
            "code",
            "name",
            "category",
            "category_id",
            "status",
            "location",
            "purchase_date",
            "price",
            "vendor",
            "spec",
            "usable",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EquipmentStatusChangeSerializer(serializers.Serializer):
    to_status = serializers.ChoiceField(choices=EquipmentStatus.choices)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=256)
    remark = serializers.CharField(required=False, allow_blank=True)


class EquipmentStatusLogSerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(source="changed_by.username", read_only=True)

    class Meta:
        model = EquipmentStatusLog
        fields = [
            "id",
            "equipment_id",
            "from_status",
            "to_status",
            "changed_by",
            "changed_by_username",
            "reason",
            "remark",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
