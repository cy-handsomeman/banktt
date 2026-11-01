from rest_framework import serializers
from apps.sys_user_role.models import SysUserRole


class SysUserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysUserRole
        fields = '__all__'
