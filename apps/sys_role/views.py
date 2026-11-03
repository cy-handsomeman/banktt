from django.shortcuts import render
from rest_framework import viewsets
from apps.sys_role.models import SysRole
from apps.sys_role.serializers import SysRoleSerializer


def sys_role_list(request):
    return render(request, 'sys_role.html')


class SysRoleViewSet(viewsets.ModelViewSet):
    queryset = SysRole.objects.all()
    serializer_class = SysRoleSerializer
    filterset_fields = ['role_id', 'role_name']
    search_fields = ['role_name', 'description']
