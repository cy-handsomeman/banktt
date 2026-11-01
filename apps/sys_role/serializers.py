from rest_framework import serializers
from apps.sys_role.models import SysRole


class SysRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysRole
        fields = '__all__'
