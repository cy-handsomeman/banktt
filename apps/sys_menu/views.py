from django.db import transaction
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from apps.sys_menu.models import SysMenu
from apps.sys_menu.serializers import SysMenuSerializer
from apps.sys_role_menu.models import SysRoleMenu
from apps.sys_user.permissions import IsSuperAdmin


def menu_list(request):
    return render(request, 'sys_menu.html')


class SysMenuViewSet(viewsets.ModelViewSet):
    queryset = SysMenu.objects.all().order_by('parent_id', 'sort_order', 'menu_id')
    serializer_class = SysMenuSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['menu_id', 'parent_id', 'menu_name', 'menu_group']
    search_fields = ['menu_name', 'menu_url', 'remark']

    def perform_destroy(self, instance):
        # 有子菜单时删除会产生孤儿，必须先处理子菜单
        child_count = SysMenu.objects.filter(parent_id=instance.menu_id).count()
        if child_count:
            raise ValidationError({
                'detail': f'菜单「{instance.menu_name}」下还有 {child_count} 个子菜单，请先删除子菜单'
            })
        # 已授权给角色的菜单不能静默级联删除，必须先解除授权
        bind_count = SysRoleMenu.objects.filter(menu_id=instance.menu_id).count()
        if bind_count:
            raise ValidationError({
                'detail': f'菜单「{instance.menu_name}」已授权给 {bind_count} 个角色，请先解除授权'
            })
        with transaction.atomic():
            instance.delete()
