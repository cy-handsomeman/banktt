from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from apps.sys_user.models import SysUser

#传输数据防止数据丢失
class SysUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysUser
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
        }

    def validate(self, attrs):
        """新增时必须携带密码；修改时可不传（保持原密码）"""
        if self.instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'password': '密码不能为空'})
        return attrs

    def validate_password(self, value):
        """入库前统一做哈希，禁止明文落库"""
        if not value:
            return value
        return make_password(value)

    def validate_pid(self, value):
        """身份证号唯一校验：新增与编辑时都排除自身"""
        queryset = SysUser.objects.filter(pid=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('该身份证号已存在，请勿重复录入')
        return value
