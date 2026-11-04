from rest_framework import viewsets
from apps.sys_menu.models import SysMenu
from apps.sys_menu.serializers import SysMenuSerializer
from apps.sys_user.permissions import IsSuperAdmin


class SysMenuViewSet(viewsets.ModelViewSet):
    queryset = SysMenu.objects.all().order_by('parent_id', 'sort_order', 'menu_id')
    serializer_class = SysMenuSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['menu_id', 'parent_id', 'menu_name']
    search_fields = ['menu_name', 'menu_url', 'remark']
