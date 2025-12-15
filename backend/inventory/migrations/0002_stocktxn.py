from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("borrowing", "0001_initial"),
        ("accounts", "0002_role_userrole"),
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="StockTxn",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("IN", "In"), ("CONSUME", "Consume")], max_length=16)),
                ("qty", models.PositiveIntegerField()),
                ("remark", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("consumable", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="txns", to="inventory.consumable")),
                ("performed_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="stock_txns", to="accounts.user")),
                ("related_request", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="stock_txns", to="borrowing.borrowrequest")),
            ],
            options={
                "indexes": [models.Index(fields=["consumable", "type", "created_at"], name="inventory_s_consuma_c289c1_idx")],
            },
        ),
    ]
