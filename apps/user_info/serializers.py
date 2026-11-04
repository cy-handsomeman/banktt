import re

from rest_framework import serializers

from apps.user_info.models import UserInfo

PID_PATTERN = re.compile(r'^\d{17}[\dXx]$')
TELEPHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')


class UserSerializer(serializers.ModelSerializer):
    """用户表序列化"""
    class Meta:
        model = UserInfo
        fields = '__all__'

    def validate_pid(self, value):
        """身份证号格式与唯一校验：编辑时历史值保持不变则不拦截"""
        if self.instance is None or value != self.instance.pid:
            if not PID_PATTERN.fullmatch(value or ''):
                raise serializers.ValidationError('身份证号必须为 18 位（末位可为 X）')
        queryset = UserInfo.objects.filter(pid=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('该身份证号已存在，请勿重复录入')
        return value

    def validate_telephone(self, value):
        """联系电话格式校验：编辑时历史值保持不变则不拦截"""
        if self.instance is None or value != self.instance.telephone:
            if not TELEPHONE_PATTERN.fullmatch(value or ''):
                raise serializers.ValidationError('联系电话必须为 11 位手机号')
        return value
