from django.contrib.auth.management.commands import createsuperuser
from django.contrib.auth import get_user_model
from django.core.management import call_command


class Command(createsuperuser.Command):
    help = '创建超级管理员并自动分配ADMIN角色'

    def handle(self, *args, **options):
        # 调用父类的handle方法创建超级用户
        super().handle(*args, **options)
        
        # 获取用户模型
        User = get_user_model()
        
        # 获取刚创建的超级用户（通过用户名）
        username = options.get('username')
        if not username:
            # 如果没有提供用户名，提示用户输入
            username = input('请输入超级用户名: ')
        
        try:
            user = User.objects.get(username=username)
            
            # 获取或创建ADMIN角色
            Role = self.get_role_model()
            admin_role, created = Role.objects.get_or_create(
                code='ADMIN',
                defaults={
                    'name': '管理员'
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'已创建ADMIN角色: {admin_role.name}'))
            
            # 分配ADMIN角色给超级用户
            UserRole = self.get_user_role_model()
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=admin_role
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'成功为超级用户 "{username}" 分配ADMIN角色'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'超级用户 "{username}" 已拥有ADMIN角色'
                    )
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'未找到用户 "{username}"，无法分配角色'
                )
            )
    
    def get_role_model(self):
        """获取Role模型"""
        from django.apps import apps
        return apps.get_model('accounts', 'Role')
    
    def get_user_role_model(self):
        """获取UserRole模型"""
        from django.apps import apps
        return apps.get_model('accounts', 'UserRole')