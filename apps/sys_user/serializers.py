from rest_framework import serializers
from apps.sys_user.models import SysUser

#传输数据防止数据丢失
class SysUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysUser
        fields = '__all__'
