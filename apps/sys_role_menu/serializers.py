from rest_framework import serializers
from apps.sys_role_menu.models import SysRoleMenu


class SysRoleMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysRoleMenu
        fields = '__all__'
