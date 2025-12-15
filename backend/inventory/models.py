from django.db import models
from django.utils import timezone

from accounts.models import User


class EquipmentStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Available"
    RESERVED = "RESERVED", "Reserved"
    BORROWED = "BORROWED", "Borrowed"
    OUT = "OUT", "Out (Legacy)"
    RETURN_PENDING = "RETURN_PENDING", "Return Pending"
    MAINTENANCE = "MAINTENANCE", "Maintenance"
    DISCARDED = "DISCARDED", "Discarded"


class EquipmentCategory(models.Model):
    name = models.CharField(max_length=128, unique=True)
    code = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "equipment_category"

    def __str__(self):
        return self.code


class Equipment(models.Model):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    category = models.ForeignKey(EquipmentCategory, on_delete=models.PROTECT, related_name="equipment")
    status = models.CharField(max_length=32, choices=EquipmentStatus.choices, default=EquipmentStatus.AVAILABLE)
    location = models.CharField(max_length=128, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    vendor = models.CharField(max_length=128, blank=True)
    spec = models.CharField(max_length=256, blank=True)
    usable = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "equipment"
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.code


class EquipmentStatusLog(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="status_logs")
    from_status = models.CharField(max_length=32, choices=EquipmentStatus.choices)
    to_status = models.CharField(max_length=32, choices=EquipmentStatus.choices)
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="equipment_status_changes")
    reason = models.CharField(max_length=256, blank=True)
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "equipment_status_log"
        indexes = [
            models.Index(fields=["equipment"]),
        ]


class Consumable(models.Model):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    unit = models.CharField(max_length=32)
    category = models.CharField(max_length=64, blank=True)
    safety_stock = models.PositiveIntegerField(default=0)
    current_stock = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "consumable"
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["current_stock"]),
        ]

    def __str__(self):
        return self.code


class StockTxnType(models.TextChoices):
    IN = "IN", "In"
    OUT = "OUT", "Out"


class StockTxnStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class StockTxn(models.Model):
    consumable = models.ForeignKey(Consumable, on_delete=models.CASCADE, related_name="txns")
    type = models.CharField(max_length=16, choices=StockTxnType.choices)
    status = models.CharField(max_length=16, choices=StockTxnStatus.choices, default=StockTxnStatus.PENDING)
    qty = models.PositiveIntegerField()
    related_request = models.ForeignKey(
        "borrowing.BorrowRequest", on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_txns"
    )
    performed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="stock_txns")
    reviewed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True, related_name="reviewed_stock_txns"
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    remark = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stock_txn"
        indexes = [
            models.Index(fields=["consumable", "type", "created_at"]),
            models.Index(fields=["status"]),
        ]
