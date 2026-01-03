from django.db import migrations


def create_admin_role(apps, schema_editor):
    """创建ADMIN角色"""
    Role = apps.get_model('accounts', 'Role')
    
    # 创建ADMIN角色
    Role.objects.get_or_create(
        code='ADMIN',
        defaults={
            'name': '管理员'
        }
    )


def reverse_create_admin_role(apps, schema_editor):
    """回滚：删除ADMIN角色"""
    Role = apps.get_model('accounts', 'Role')
    Role.objects.filter(code='ADMIN').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0005_fix_user_updated_at_column'),
    ]

    operations = [
        migrations.RunPython(create_admin_role, reverse_create_admin_role),
    ]