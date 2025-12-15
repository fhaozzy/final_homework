from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0002_role_userrole"),
    ]

    operations = [
        migrations.CreateModel(
            name="Consumable",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=128)),
                ("unit", models.CharField(max_length=32)),
                ("category", models.CharField(blank=True, max_length=64)),
                ("safety_stock", models.PositiveIntegerField(default=0)),
                ("current_stock", models.PositiveIntegerField(default=0)),
                ("location", models.CharField(blank=True, max_length=128)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "indexes": [models.Index(fields=["code"], name="inventory_c_code_1718ae_idx"), models.Index(fields=["current_stock"], name="inventory_c_current_54a304_idx")],
            },
        ),
        migrations.CreateModel(
            name="EquipmentCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128, unique=True)),
                ("code", models.CharField(max_length=64, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Equipment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=128)),
                ("status", models.CharField(choices=[("AVAILABLE", "Available"), ("RESERVED", "Reserved"), ("OUT", "Out"), ("RETURN_PENDING", "Return Pending"), ("MAINTENANCE", "Maintenance"), ("DISCARDED", "Discarded")], default="AVAILABLE", max_length=32)),
                ("location", models.CharField(blank=True, max_length=128)),
                ("purchase_date", models.DateField(blank=True, null=True)),
                ("price", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("vendor", models.CharField(blank=True, max_length=128)),
                ("spec", models.CharField(blank=True, max_length=256)),
                ("usable", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="equipment", to="inventory.equipmentcategory")),
            ],
            options={
                "indexes": [models.Index(fields=["category"], name="inventory_e_categor_9b2228_idx"), models.Index(fields=["status"], name="inventory_e_status_6804f8_idx")],
            },
        ),
        migrations.CreateModel(
            name="EquipmentStatusLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_status", models.CharField(choices=[("AVAILABLE", "Available"), ("RESERVED", "Reserved"), ("OUT", "Out"), ("RETURN_PENDING", "Return Pending"), ("MAINTENANCE", "Maintenance"), ("DISCARDED", "Discarded")], max_length=32)),
                ("to_status", models.CharField(choices=[("AVAILABLE", "Available"), ("RESERVED", "Reserved"), ("OUT", "Out"), ("RETURN_PENDING", "Return Pending"), ("MAINTENANCE", "Maintenance"), ("DISCARDED", "Discarded")], max_length=32)),
                ("reason", models.CharField(blank=True, max_length=256)),
                ("remark", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("changed_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="equipment_status_changes", to="accounts.user")),
                ("equipment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="status_logs", to="inventory.equipment")),
            ],
            options={
                "indexes": [models.Index(fields=["equipment"], name="inventory_e_equipme_745b88_idx")],
            },
        ),
    ]
