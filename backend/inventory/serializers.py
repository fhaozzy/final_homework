from rest_framework import serializers

from inventory.models import (
    Consumable,
    Equipment,
    EquipmentCategory,
    EquipmentStatus,
    EquipmentStatusLog,
    StockTxn,
)


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


class ConsumableSerializer(serializers.ModelSerializer):
    current_qty = serializers.IntegerField(source="current_stock", read_only=True)

    class Meta:
        model = Consumable
        fields = [
            "id",
            "code",
            "name",
            "unit",
            "category",
            "safety_stock",
            "current_qty",
            "location",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "current_qty", "created_at", "updated_at"]


class StockInSerializer(serializers.Serializer):
    consumable_id = serializers.PrimaryKeyRelatedField(source="consumable", queryset=Consumable.objects.all())
    qty = serializers.IntegerField(min_value=1)
    remark = serializers.CharField(required=False, allow_blank=True, max_length=255)


class StockOutSerializer(serializers.Serializer):
    consumable_id = serializers.PrimaryKeyRelatedField(source="consumable", queryset=Consumable.objects.all())
    qty = serializers.IntegerField(min_value=1)
    remark = serializers.CharField(required=False, allow_blank=True, max_length=255)


class StockTxnSerializer(serializers.ModelSerializer):
    consumable_code = serializers.CharField(source="consumable.code", read_only=True)
    consumable_name = serializers.CharField(source="consumable.name", read_only=True)
    performed_by_username = serializers.CharField(source="performed_by.username", read_only=True)
    reviewed_by_username = serializers.CharField(source="reviewed_by.username", read_only=True)

    class Meta:
        model = StockTxn
        fields = [
            "id",
            "consumable_id",
            "consumable_code",
            "consumable_name",
            "type",
            "status",
            "qty",
            "remark",
            "performed_by",
            "performed_by_username",
            "reviewed_by",
            "reviewed_by_username",
            "decided_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
