from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from accounts.permissions import IsAdminOrReadOnly, IsAdminUser, is_admin_user
from inventory.models import (
    Consumable,
    Equipment,
    EquipmentCategory,
    EquipmentStatus,
    EquipmentStatusLog,
    StockTxn,
    StockTxnStatus,
    StockTxnType,
)
from inventory.serializers import (
    ConsumableSerializer,
    EquipmentCategorySerializer,
    EquipmentSerializer,
    EquipmentStatusChangeSerializer,
    EquipmentStatusLogSerializer,
    StockInSerializer,
    StockOutSerializer,
    StockTxnSerializer,
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
        return to_status in {EquipmentStatus.RESERVED, EquipmentStatus.BORROWED}

    if from_status == EquipmentStatus.RESERVED:
        return to_status in {EquipmentStatus.BORROWED, EquipmentStatus.OUT, EquipmentStatus.AVAILABLE}

    if from_status == EquipmentStatus.BORROWED:
        return to_status in {EquipmentStatus.RETURN_PENDING, EquipmentStatus.AVAILABLE}

    if from_status == EquipmentStatus.OUT:
        return to_status in {EquipmentStatus.RETURN_PENDING, EquipmentStatus.AVAILABLE}

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


class ConsumableViewSet(ModelViewSet):
    queryset = Consumable.objects.all().order_by("-id")
    serializer_class = ConsumableSerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=False, methods=["get"], url_path="warnings")
    def warnings(self, request):
        qs = self.get_queryset().filter(current_stock__lt=F("safety_stock")).order_by("current_stock", "id")
        return Response(ConsumableSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class StockTxnViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    queryset = StockTxn.objects.select_related("consumable", "performed_by", "reviewed_by").order_by("-id")
    serializer_class = StockTxnSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in {"stock_in", "approve", "reject"}:
            return [IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        if is_admin_user(self.request.user):
            return qs
        return qs.filter(performed_by=self.request.user)

    @action(detail=False, methods=["post"], url_path="in")
    @transaction.atomic
    def stock_in(self, request):
        serializer = StockInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        consumable = serializer.validated_data["consumable"]
        qty = serializer.validated_data["qty"]
        remark = serializer.validated_data.get("remark", "")
        now = timezone.now()

        consumable = Consumable.objects.select_for_update().get(pk=consumable.pk)
        Consumable.objects.filter(pk=consumable.pk).update(current_stock=F("current_stock") + qty, updated_at=now)

        txn = StockTxn.objects.create(
            consumable=consumable,
            type=StockTxnType.IN,
            status=StockTxnStatus.APPROVED,
            qty=qty,
            performed_by=request.user,
            reviewed_by=request.user,
            decided_at=now,
            remark=remark,
        )

        return Response(StockTxnSerializer(txn).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="out")
    def stock_out(self, request):
        serializer = StockOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        consumable = serializer.validated_data["consumable"]
        qty = serializer.validated_data["qty"]
        remark = serializer.validated_data.get("remark", "")

        txn = StockTxn.objects.create(
            consumable=consumable,
            type=StockTxnType.OUT,
            status=StockTxnStatus.PENDING,
            qty=qty,
            performed_by=request.user,
            remark=remark,
        )
        return Response(StockTxnSerializer(txn).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="approve")
    @transaction.atomic
    def approve(self, request, pk=None):
        txn = StockTxn.objects.select_for_update().select_related("consumable").get(pk=pk)
        if txn.type != StockTxnType.OUT:
            raise ValidationError({"type": f"Only OUT txn can be approved, got {txn.type}."})
        if txn.status != StockTxnStatus.PENDING:
            raise ValidationError({"status": f"Txn must be PENDING, got {txn.status}."})

        now = timezone.now()
        consumable = Consumable.objects.select_for_update().get(pk=txn.consumable_id)
        updated = Consumable.objects.filter(pk=consumable.pk, current_stock__gte=txn.qty).update(
            current_stock=F("current_stock") - txn.qty, updated_at=now
        )
        if updated != 1:
            raise ValidationError({"stock": "Insufficient stock."})

        txn.status = StockTxnStatus.APPROVED
        txn.reviewed_by = request.user
        txn.decided_at = now
        txn.save(update_fields=["status", "reviewed_by", "decided_at", "updated_at"])

        return Response(StockTxnSerializer(txn).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="reject")
    @transaction.atomic
    def reject(self, request, pk=None):
        txn = StockTxn.objects.select_for_update().get(pk=pk)
        if txn.type != StockTxnType.OUT:
            raise ValidationError({"type": f"Only OUT txn can be rejected, got {txn.type}."})
        if txn.status != StockTxnStatus.PENDING:
            raise ValidationError({"status": f"Txn must be PENDING, got {txn.status}."})

        now = timezone.now()
        txn.status = StockTxnStatus.REJECTED
        txn.reviewed_by = request.user
        txn.decided_at = now
        txn.save(update_fields=["status", "reviewed_by", "decided_at", "updated_at"])
        return Response(StockTxnSerializer(txn).data, status=status.HTTP_200_OK)
