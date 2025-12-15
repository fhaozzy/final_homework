from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from borrowing.models import (
    BorrowApproval,
    BorrowItem,
    BorrowItemStatus,
    BorrowRequest,
    RequestStatus,
    RequestType,
    ReturnCondition,
)
from inventory.models import Equipment, EquipmentStatus


class EquipmentBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ["id", "code", "name", "status", "category_id", "location", "usable"]


class BorrowItemSerializer(serializers.ModelSerializer):
    equipment = EquipmentBriefSerializer(read_only=True)

    class Meta:
        model = BorrowItem
        fields = [
            "id",
            "item_type",
            "equipment",
            "equipment_id",
            "qty",
            "status",
            "out_at",
            "due_at",
            "return_submitted_at",
            "return_checked_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class BorrowApprovalSerializer(serializers.ModelSerializer):
    approver_username = serializers.CharField(source="approver.username", read_only=True)

    class Meta:
        model = BorrowApproval
        fields = ["id", "decision", "comment", "decided_at", "approver", "approver_username", "created_at", "updated_at"]
        read_only_fields = fields


class BorrowRequestSerializer(serializers.ModelSerializer):
    applicant_username = serializers.CharField(source="applicant.username", read_only=True)
    approver_username = serializers.CharField(source="approver.username", read_only=True)
    items = BorrowItemSerializer(many=True, read_only=True)
    approval = BorrowApprovalSerializer(read_only=True)

    class Meta:
        model = BorrowRequest
        fields = [
            "id",
            "type",
            "status",
            "purpose",
            "expected_return_date",
            "submitted_at",
            "approved_at",
            "rejected_at",
            "remark",
            "applicant",
            "applicant_username",
            "approver",
            "approver_username",
            "created_at",
            "updated_at",
            "items",
            "approval",
        ]
        read_only_fields = fields


class BorrowRequestCreateItemSerializer(serializers.Serializer):
    equipment_id = serializers.PrimaryKeyRelatedField(source="equipment", queryset=Equipment.objects.all())


class BorrowRequestCreateSerializer(serializers.Serializer):
    purpose = serializers.CharField(required=False, allow_blank=True, max_length=255)
    expected_return_date = serializers.DateField(required=False, allow_null=True)
    remark = serializers.CharField(required=False, allow_blank=True)
    items = BorrowRequestCreateItemSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("items must not be empty")

        equipment_ids = [it["equipment"].id for it in items]
        if len(equipment_ids) != len(set(equipment_ids)):
            raise serializers.ValidationError("duplicated equipment_id")

        equipments = Equipment.objects.filter(id__in=equipment_ids).only("id", "status")
        status_by_id = {e.id: e.status for e in equipments}

        invalid = [eid for eid in equipment_ids if status_by_id.get(eid) != EquipmentStatus.AVAILABLE]
        if invalid:
            raise serializers.ValidationError(f"equipment not AVAILABLE: {invalid}")

        return items

    @transaction.atomic
    def create(self, validated_data):
        request_user = self.context["request"].user
        now = timezone.now()

        borrow_request = BorrowRequest.objects.create(
            applicant=request_user,
            type=RequestType.EQUIPMENT,
            status=RequestStatus.REQUESTED,
            purpose=validated_data.get("purpose", ""),
            expected_return_date=validated_data.get("expected_return_date"),
            submitted_at=now,
            remark=validated_data.get("remark", ""),
        )

        items = validated_data["items"]
        BorrowItem.objects.bulk_create(
            [
                BorrowItem(
                    request=borrow_request,
                    item_type=BorrowItem.ItemType.EQUIPMENT,
                    equipment=item["equipment"],
                    qty=1,
                    status=BorrowItemStatus.PENDING,
                )
                for item in items
            ]
        )

        return borrow_request


class BorrowApprovalActionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)


class BorrowReturnItemSerializer(serializers.Serializer):
    borrow_item_id = serializers.IntegerField()
    condition = serializers.ChoiceField(choices=ReturnCondition.choices, default=ReturnCondition.GOOD)
    fee = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    remark = serializers.CharField(required=False, allow_blank=True)


class BorrowReturnSerializer(serializers.Serializer):
    items = BorrowReturnItemSerializer(many=True, required=False)
