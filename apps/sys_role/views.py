from django.shortcuts import render
from rest_framework import viewsets
from apps.sys_role.models import SysRole
from apps.sys_role.serializers import SysRoleSerializer
from apps.sys_user.permissions import IsSuperAdminOrReadOnly


def sys_role_list(request):
    return render(request, 'sys_role.html')


class SysRoleViewSet(viewsets.ModelViewSet):
    queryset = SysRole.objects.all().order_by('role_id')
    serializer_class = SysRoleSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filterset_fields = ['role_id', 'role_name']
    search_fields = ['role_name', 'description']
