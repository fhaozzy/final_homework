from django.db import transaction
from django.utils import timezone
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from accounts.permissions import IsAdminUser, is_admin_user, is_teacher_user
from borrowing.models import (
    BorrowApproval,
    BorrowApprovalDecision,
    BorrowItem,
    BorrowItemStatus,
    BorrowRequest,
    RequestStatus,
    RequestType,
    ReturnCondition,
    ReturnRecord,
)
from borrowing.serializers import (
    BorrowApprovalActionSerializer,
    BorrowRequestCreateSerializer,
    BorrowRequestSerializer,
    BorrowReturnSerializer,
)
from inventory.models import Equipment, EquipmentStatus, EquipmentStatusLog


class BorrowRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = (
        BorrowRequest.objects.select_related("applicant", "approver")
        .prefetch_related("items__equipment", "approval")
        .order_by("-id")
    )

    def get_permissions(self):
        if self.action in {"approve", "reject", "checkout", "return_request"}:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowRequestCreateSerializer
        if self.action == "approve":
            return BorrowApprovalActionSerializer
        if self.action == "reject":
            return BorrowApprovalActionSerializer
        if self.action == "return_request":
            return BorrowReturnSerializer
        return BorrowRequestSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_admin_user(self.request.user) or is_teacher_user(self.request.user):
            return queryset
        return queryset.filter(applicant=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        borrow_request = serializer.save()
        borrow_request = (
            BorrowRequest.objects.select_related("applicant", "approver")
            .prefetch_related("items__equipment", "approval")
            .get(pk=borrow_request.pk)
        )
        return Response(BorrowRequestSerializer(borrow_request).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="approve")
    @transaction.atomic
    def approve(self, request, pk=None):
        borrow_request = BorrowRequest.objects.select_for_update().get(pk=pk)
        if borrow_request.type != RequestType.EQUIPMENT:
            raise ValidationError({"type": "Only EQUIPMENT requests are supported by this endpoint."})

        if borrow_request.status != RequestStatus.REQUESTED:
            raise ValidationError({"status": f"Request must be REQUESTED, got {borrow_request.status}."})

        if BorrowApproval.objects.filter(request=borrow_request).exists():
            raise ValidationError({"approval": "Request already has approval record."})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.validated_data.get("comment", "")
        now = timezone.now()

        BorrowApproval.objects.create(
            request=borrow_request,
            approver=request.user,
            decision=BorrowApprovalDecision.APPROVED,
            comment=comment,
            decided_at=now,
        )

        borrow_request.status = RequestStatus.APPROVED
        borrow_request.approved_at = now
        borrow_request.rejected_at = None
        borrow_request.approver = request.user
        borrow_request.save(update_fields=["status", "approved_at", "rejected_at", "approver", "updated_at"])

        borrow_request = self.get_queryset().get(pk=borrow_request.pk)
        return Response(BorrowRequestSerializer(borrow_request).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="reject")
    @transaction.atomic
    def reject(self, request, pk=None):
        borrow_request = BorrowRequest.objects.select_for_update().get(pk=pk)
        if borrow_request.type != RequestType.EQUIPMENT:
            raise ValidationError({"type": "Only EQUIPMENT requests are supported by this endpoint."})

        if borrow_request.status != RequestStatus.REQUESTED:
            raise ValidationError({"status": f"Request must be REQUESTED, got {borrow_request.status}."})

        if BorrowApproval.objects.filter(request=borrow_request).exists():
            raise ValidationError({"approval": "Request already has approval record."})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.validated_data.get("comment", "")
        now = timezone.now()

        BorrowApproval.objects.create(
            request=borrow_request,
            approver=request.user,
            decision=BorrowApprovalDecision.REJECTED,
            comment=comment,
            decided_at=now,
        )

        borrow_request.status = RequestStatus.REJECTED
        borrow_request.rejected_at = now
        borrow_request.approved_at = None
        borrow_request.approver = request.user
        borrow_request.save(update_fields=["status", "rejected_at", "approved_at", "approver", "updated_at"])

        borrow_request = self.get_queryset().get(pk=borrow_request.pk)
        return Response(BorrowRequestSerializer(borrow_request).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="checkout")
    @transaction.atomic
    def checkout(self, request, pk=None):
        borrow_request = (
            BorrowRequest.objects.select_for_update()
            .prefetch_related("items")
            .get(pk=pk)
        )
        if borrow_request.type != RequestType.EQUIPMENT:
            raise ValidationError({"type": "Only EQUIPMENT requests are supported by this endpoint."})

        if borrow_request.status != RequestStatus.APPROVED:
            raise ValidationError({"status": f"Request must be APPROVED, got {borrow_request.status}."})

        items = list(borrow_request.items.all())
        if not items:
            raise ValidationError({"items": "Request has no items."})

        equipment_ids = [it.equipment_id for it in items if it.item_type == BorrowItem.ItemType.EQUIPMENT]
        if not equipment_ids or any(eid is None for eid in equipment_ids):
            raise ValidationError({"items": "Equipment items required."})

        equipment_ids_sorted = sorted(set(equipment_ids))
        equipments = list(Equipment.objects.select_for_update().filter(id__in=equipment_ids_sorted).order_by("id"))
        if len(equipments) != len(equipment_ids_sorted):
            raise ValidationError({"items": "Some equipment not found."})

        not_available = [e.id for e in equipments if e.status != EquipmentStatus.AVAILABLE]
        if not_available:
            raise ValidationError({"equipment": f"Only AVAILABLE equipment can be checked out: {not_available}"})

        now = timezone.now()
        logs = []
        for equipment in equipments:
            from_status = equipment.status
            equipment.status = EquipmentStatus.BORROWED
            equipment.save(update_fields=["status", "updated_at"])
            logs.append(
                EquipmentStatusLog(
                    equipment=equipment,
                    from_status=from_status,
                    to_status=EquipmentStatus.BORROWED,
                    changed_by=request.user,
                    reason="checkout",
                    remark=f"borrow_request:{borrow_request.id}",
                )
            )

        EquipmentStatusLog.objects.bulk_create(logs)

        BorrowItem.objects.filter(id__in=[it.id for it in items]).update(
            status=BorrowItemStatus.OUT,
            out_at=now,
            updated_at=now,
        )

        borrow_request.status = RequestStatus.OUT
        borrow_request.save(update_fields=["status", "updated_at"])

        borrow_request = (
            BorrowRequest.objects.select_related("applicant", "approver")
            .prefetch_related("items__equipment", "approval")
            .get(pk=borrow_request.pk)
        )
        return Response(BorrowRequestSerializer(borrow_request).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="return")
    @transaction.atomic
    def return_request(self, request, pk=None):
        borrow_request = (
            BorrowRequest.objects.select_for_update()
            .prefetch_related("items")
            .get(pk=pk)
        )
        if borrow_request.type != RequestType.EQUIPMENT:
            raise ValidationError({"type": "Only EQUIPMENT requests are supported by this endpoint."})

        if borrow_request.status != RequestStatus.OUT:
            raise ValidationError({"status": f"Request must be OUT, got {borrow_request.status}."})

        items = list(borrow_request.items.all())
        if not items:
            raise ValidationError({"items": "Request has no items."})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return_items = serializer.validated_data.get("items")

        item_by_id = {it.id: it for it in items}
        if return_items:
            item_ids = [it["borrow_item_id"] for it in return_items]
            unknown = [bid for bid in item_ids if bid not in item_by_id]
            if unknown:
                raise ValidationError({"items": f"borrow_item_id not in this request: {unknown}"})

        equipment_ids = sorted({it.equipment_id for it in items if it.equipment_id is not None})
        equipments = list(Equipment.objects.select_for_update().filter(id__in=equipment_ids).order_by("id"))
        if len(equipments) != len(equipment_ids):
            raise ValidationError({"items": "Some equipment not found."})

        now = timezone.now()
        return_records = []
        logs = []

        existing_return_records = set(
            ReturnRecord.objects.filter(borrow_item_id__in=item_by_id.keys()).values_list("borrow_item_id", flat=True)
        )
        if existing_return_records:
            raise ValidationError({"return_record": f"Already returned: {sorted(existing_return_records)}"})

        defaults = {it.id: {"condition": ReturnCondition.GOOD, "fee": 0, "remark": ""} for it in items}
        if return_items:
            for ri in return_items:
                defaults[ri["borrow_item_id"]] = {
                    "condition": ri.get("condition", ReturnCondition.GOOD),
                    "fee": ri.get("fee", 0),
                    "remark": ri.get("remark", ""),
                }

        for equipment in equipments:
            from_status = equipment.status
            equipment.status = EquipmentStatus.AVAILABLE
            equipment.save(update_fields=["status", "updated_at"])
            logs.append(
                EquipmentStatusLog(
                    equipment=equipment,
                    from_status=from_status,
                    to_status=EquipmentStatus.AVAILABLE,
                    changed_by=request.user,
                    reason="return",
                    remark=f"borrow_request:{borrow_request.id}",
                )
            )

        EquipmentStatusLog.objects.bulk_create(logs)

        for item in items:
            meta = defaults[item.id]
            return_records.append(
                ReturnRecord(
                    borrow_item_id=item.id,
                    checked_by=request.user,
                    condition=meta["condition"],
                    fee=meta["fee"],
                    remark=meta["remark"],
                    checked_at=now,
                )
            )

        ReturnRecord.objects.bulk_create(return_records)

        BorrowItem.objects.filter(id__in=item_by_id.keys()).update(
            status=BorrowItemStatus.RETURN_ACCEPTED,
            return_checked_at=now,
            updated_at=now,
        )

        borrow_request.status = RequestStatus.CLOSED
        borrow_request.save(update_fields=["status", "updated_at"])

        borrow_request = (
            BorrowRequest.objects.select_related("applicant", "approver")
            .prefetch_related("items__equipment", "approval")
            .get(pk=borrow_request.pk)
        )
        return Response(BorrowRequestSerializer(borrow_request).data, status=status.HTTP_200_OK)
