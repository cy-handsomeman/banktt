from rest_framework import viewsets
from apps.sys_menu.models import SysMenu
from apps.sys_menu.serializers import SysMenuSerializer


class SysMenuViewSet(viewsets.ModelViewSet):
    queryset = SysMenu.objects.all()
    serializer_class = SysMenuSerializer
    filterset_fields = ['menu_id', 'parent_id', 'menu_name']
    search_fields = ['menu_name', 'menu_url', 'remark']
