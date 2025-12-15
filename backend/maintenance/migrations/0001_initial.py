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
            name="Maintenance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=128)),
                ("description", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("OPEN", "Open"), ("IN_PROGRESS", "In Progress"), ("DONE", "Done")], default="OPEN", max_length=16)),
                ("cost", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="maintenance_tasks", to="accounts.user")),
                ("equipment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="maintenance_records", to="inventory.equipment")),
            ],
            options={
                "indexes": [models.Index(fields=["equipment"], name="maintenance_equipment_4fb533_idx"), models.Index(fields=["status"], name="maintenance_status_a7d250_idx")],
            },
        ),
    ]
