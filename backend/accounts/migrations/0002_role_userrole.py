from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Role",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="UserRole",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("role", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_roles", to="accounts.role")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_roles", to="accounts.user")),
            ],
            options={
                "indexes": [models.Index(fields=["user"], name="accounts_us_user_id_1e7c31_idx"), models.Index(fields=["role"], name="accounts_us_role_id_33dd5b_idx")],
                "constraints": [models.UniqueConstraint(fields=("user", "role"), name="uniq_user_role")],
            },
        ),
    ]
