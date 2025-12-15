from django.db import models
from django.utils import timezone

from accounts.models import User
from inventory.models import Equipment, Consumable


class RequestType(models.TextChoices):
    EQUIPMENT = "EQUIPMENT", "Equipment"
    CONSUMABLE = "CONSUMABLE", "Consumable"


class RequestStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Requested"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    OUT = "OUT", "Out"
    CLOSED = "CLOSED", "Closed"


class BorrowItemStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    OUT = "OUT", "Out"
    RETURN_PENDING = "RETURN_PENDING", "Return Pending"
    RETURN_ACCEPTED = "RETURN_ACCEPTED", "Return Accepted"
    RETURN_REJECTED = "RETURN_REJECTED", "Return Rejected"


class BorrowRequest(models.Model):
    applicant = models.ForeignKey(User, on_delete=models.PROTECT, related_name="borrow_requests")
    type = models.CharField(max_length=16, choices=RequestType.choices)
    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.REQUESTED)
    purpose = models.CharField(max_length=255, blank=True)
    expected_return_date = models.DateField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    approver = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name="approved_requests")
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "borrow_request"
        indexes = [
            models.Index(fields=["applicant", "status", "type"]),
        ]

    def __str__(self):
        return f"BR-{self.id}"


class BorrowItem(models.Model):
    class ItemType(models.TextChoices):
        EQUIPMENT = "EQUIPMENT", "Equipment"
        CONSUMABLE = "CONSUMABLE", "Consumable"

    request = models.ForeignKey(BorrowRequest, on_delete=models.CASCADE, related_name="items")
    item_type = models.CharField(max_length=16, choices=ItemType.choices)
    equipment = models.ForeignKey(Equipment, null=True, blank=True, on_delete=models.PROTECT, related_name="borrow_items")
    consumable = models.ForeignKey(Consumable, null=True, blank=True, on_delete=models.PROTECT, related_name="borrow_items")
    qty = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=BorrowItemStatus.choices, default=BorrowItemStatus.PENDING)
    out_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    return_submitted_at = models.DateTimeField(null=True, blank=True)
    return_checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "borrow_item"
        constraints = [
            models.UniqueConstraint(fields=["request", "equipment"], name="uniq_request_equipment"),
        ]
        indexes = [
            models.Index(fields=["request", "status"]),
        ]


class BorrowApprovalDecision(models.TextChoices):
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class BorrowApproval(models.Model):
    request = models.OneToOneField(BorrowRequest, on_delete=models.CASCADE, related_name="approval")
    approver = models.ForeignKey(User, on_delete=models.PROTECT, related_name="borrow_approvals")
    decision = models.CharField(max_length=16, choices=BorrowApprovalDecision.choices)
    comment = models.TextField(blank=True)
    decided_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "borrow_approval"


class ReturnCondition(models.TextChoices):
    GOOD = "GOOD", "Good"
    DAMAGED = "DAMAGED", "Damaged"
    LOST = "LOST", "Lost"


class ReturnRecord(models.Model):
    borrow_item = models.OneToOneField(BorrowItem, on_delete=models.CASCADE, related_name="return_record")
    checked_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="return_records")
    condition = models.CharField(max_length=16, choices=ReturnCondition.choices)
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remark = models.TextField(blank=True)
    checked_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "return_record"
