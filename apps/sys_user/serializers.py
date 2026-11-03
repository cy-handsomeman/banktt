from rest_framework import serializers
from apps.sys_user.models import SysUser

#传输数据防止数据丢失
class SysUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysUser
        fields = '__all__'

    def validate_pid(self, value):
        """身份证号唯一校验：新增与编辑时都排除自身"""
        queryset = SysUser.objects.filter(pid=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('该身份证号已存在，请勿重复录入')
        return value
