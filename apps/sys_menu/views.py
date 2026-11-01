from rest_framework import viewsets
from apps.sys_menu.models import SysMenu
from apps.sys_menu.serializers import SysMenuSerializer


class SysMenuViewSet(viewsets.ModelViewSet):
    queryset = SysMenu.objects.all()
    serializer_class = SysMenuSerializer
