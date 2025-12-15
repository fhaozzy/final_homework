from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0002_role_userrole"),
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BorrowRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("EQUIPMENT", "Equipment"), ("CONSUMABLE", "Consumable")], max_length=16)),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("PENDING_APPROVAL", "Pending Approval"), ("APPROVED", "Approved"), ("REJECTED", "Rejected"), ("CANCELLED", "Cancelled")], default="DRAFT", max_length=20)),
                ("purpose", models.CharField(blank=True, max_length=255)),
                ("expected_return_date", models.DateField(blank=True, null=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("rejected_at", models.DateTimeField(blank=True, null=True)),
                ("remark", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("applicant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="borrow_requests", to="accounts.user")),
                ("approver", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="approved_requests", to="accounts.user")),
            ],
            options={
                "indexes": [models.Index(fields=["applicant", "status", "type"], name="borrowing_b_applica_036766_idx")],
            },
        ),
        migrations.CreateModel(
            name="BorrowItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("item_type", models.CharField(choices=[("EQUIPMENT", "Equipment"), ("CONSUMABLE", "Consumable")], max_length=16)),
                ("qty", models.PositiveIntegerField(default=1)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("OUT", "Out"), ("RETURN_PENDING", "Return Pending"), ("RETURN_ACCEPTED", "Return Accepted"), ("RETURN_REJECTED", "Return Rejected")], default="PENDING", max_length=20)),
                ("out_at", models.DateTimeField(blank=True, null=True)),
                ("due_at", models.DateTimeField(blank=True, null=True)),
                ("return_submitted_at", models.DateTimeField(blank=True, null=True)),
                ("return_checked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("consumable", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="borrow_items", to="inventory.consumable")),
                ("equipment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="borrow_items", to="inventory.equipment")),
                ("request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="borrowing.borrowrequest")),
            ],
            options={
                "constraints": [models.UniqueConstraint(fields=("request", "equipment"), name="uniq_request_equipment")],
                "indexes": [models.Index(fields=["request", "status"], name="borrowing_b_request_3f68b4_idx")],
            },
        ),
        migrations.CreateModel(
            name="BorrowApproval",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("decision", models.CharField(choices=[("APPROVED", "Approved"), ("REJECTED", "Rejected")], max_length=16)),
                ("comment", models.TextField(blank=True)),
                ("decided_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("approver", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="borrow_approvals", to="accounts.user")),
                ("request", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="approval", to="borrowing.borrowrequest")),
            ],
        ),
        migrations.CreateModel(
            name="ReturnRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("condition", models.CharField(choices=[("GOOD", "Good"), ("DAMAGED", "Damaged"), ("LOST", "Lost")], max_length=16)),
                ("fee", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("remark", models.TextField(blank=True)),
                ("checked_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("borrow_item", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="return_record", to="borrowing.borrowitem")),
                ("checked_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="return_records", to="accounts.user")),
            ],
        ),
    ]
