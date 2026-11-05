from django.db import transaction
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from apps.sys_role.models import SysRole
from apps.sys_role.serializers import SysRoleSerializer
from apps.sys_role_menu.models import SysRoleMenu
from apps.sys_user.permissions import IsSuperAdmin, SUPER_ADMIN_ROLE_ID
from apps.sys_user_role.models import SysUserRole


class SysRoleViewSet(viewsets.ModelViewSet):
    queryset = SysRole.objects.all().order_by('role_id')
    serializer_class = SysRoleSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['role_id', 'role_name']
    search_fields = ['role_name', 'description']

    def perform_destroy(self, instance):
        # 超管角色是系统权限的根，删除后会导致无人可授权
        if instance.role_id == SUPER_ADMIN_ROLE_ID:
            raise ValidationError({'detail': '超级管理员角色不允许删除'})
        # 角色一旦被用户或菜单引用就不能直接删除，避免外键约束报 500
        user_count = SysUserRole.objects.filter(role_id=instance.role_id).count()
        if user_count:
            raise ValidationError(
                {'detail': f'角色「{instance.role_name}」已分配给 {user_count} 个用户，请先解除分配'}
            )
        menu_count = SysRoleMenu.objects.filter(role_id=instance.role_id).count()
        if menu_count:
            raise ValidationError(
                {'detail': f'角色「{instance.role_name}」已绑定 {menu_count} 个菜单，请先解除绑定'}
            )
        with transaction.atomic():
            instance.delete()
