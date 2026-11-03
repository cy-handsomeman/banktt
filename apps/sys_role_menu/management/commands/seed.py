from django.core.management.base import BaseCommand
from django.db import transaction

from apps.sys_menu.models import SysMenu
from apps.sys_role.models import SysRole
from apps.sys_role_menu.models import SysRoleMenu
from apps.sys_user.models import SysUser
from apps.sys_user_role.models import SysUserRole


class Command(BaseCommand):
    help = '初始化角色菜单数据：为缺少菜单的角色补齐全部菜单，并为无角色用户分配默认角色'

    def handle(self, *args, **options):
        menus = list(SysMenu.objects.all().order_by('menu_id'))
        if not menus:
            self.stdout.write(self.style.WARNING('sys_menu 表为空，请先维护菜单数据'))
            return

        with transaction.atomic():
            created_bindings = 0
            for role in SysRole.objects.all().order_by('role_id'):
                bound_ids = set(
                    SysRoleMenu.objects.filter(role_id=role.role_id).values_list('menu_id', flat=True)
                )
                missing_ids = [menu.menu_id for menu in menus if menu.menu_id not in bound_ids]
                if not missing_ids:
                    self.stdout.write(f'角色 {role.role_id}（{role.role_name}）已有 {len(bound_ids)} 个菜单，跳过')
                    continue
                SysRoleMenu.objects.bulk_create(
                    [SysRoleMenu(role_id=role.role_id, menu_id=menu_id) for menu_id in missing_ids]
                )
                created_bindings += len(missing_ids)
                self.stdout.write(f'角色 {role.role_id}（{role.role_name}）新增绑定 {len(missing_ids)} 个菜单')

            default_role = SysRole.objects.exclude(role_id=1).order_by('role_id').first()
            assigned_users = 0
            if default_role is not None:
                users_with_role = set(SysUserRole.objects.values_list('user_id', flat=True))
                for user in SysUser.objects.all().order_by('user_id'):
                    if user.user_id in users_with_role:
                        continue
                    SysUserRole.objects.create(user_id=user.user_id, role_id=default_role.role_id)
                    assigned_users += 1
                if assigned_users:
                    self.stdout.write(
                        f'为 {assigned_users} 个无角色用户分配默认角色 {default_role.role_id}（{default_role.role_name}）'
                    )

        self.stdout.write(self.style.SUCCESS(
            f'完成：新增角色菜单绑定 {created_bindings} 条，分配默认角色 {assigned_users} 条'
        ))
