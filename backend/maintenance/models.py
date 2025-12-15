from django.db import models
from django.utils import timezone

from accounts.models import User
from inventory.models import Equipment


class MaintenanceStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    DONE = "DONE", "Done"


class Maintenance(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="maintenance_records")
    title = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=MaintenanceStatus.choices, default=MaintenanceStatus.OPEN)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="maintenance_tasks")
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "maintenance"
        indexes = [
            models.Index(fields=["equipment"]),
            models.Index(fields=["status"]),
        ]
