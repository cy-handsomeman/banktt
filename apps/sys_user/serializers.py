import re

from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.sys_user.models import SysUser, SysLoginLog

PID_PATTERN = re.compile(r'^\d{17}[\dXx]$')
MOBILE_PATTERN = re.compile(r'^1[3-9]\d{9}$')

#传输数据防止数据丢失
class SysUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysUser
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            # 唯一性由 validate_user_name / validate_pid 统一校验并给出中文提示，
            # 关闭 DRF 自动生成的唯一校验器，避免出现“具有 pid 的 sys user 已存在”这类模型名文案
            'user_name': {'validators': []},
            'pid': {'validators': []},
        }

    def validate(self, attrs):
        """新增时必须携带密码；修改时可不传（保持原密码）"""
        if self.instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'password': '密码不能为空'})
        return attrs

    def validate_password(self, value):
        """入库前做密码强度校验，再统一哈希，禁止明文落库"""
        if not value:
            return value
        try:
            django_validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return make_password(value)

    def validate_user_name(self, value):
        """用户名唯一校验：新增与编辑时都排除自身"""
        queryset = SysUser.objects.filter(user_name=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('该用户名已存在，请更换')
        return value

    def validate_pid(self, value):
        """身份证号格式与唯一校验：编辑时历史值保持不变则不拦截"""
        if self.instance is None or value != self.instance.pid:
            if not PID_PATTERN.fullmatch(value or ''):
                raise serializers.ValidationError('身份证号必须为 18 位（末位可为 X）')
        queryset = SysUser.objects.filter(pid=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('该身份证号已存在，请勿重复录入')
        return value

    def validate_mobile(self, value):
        """手机号格式校验：编辑时历史值保持不变则不拦截"""
        if self.instance is None or value != self.instance.mobile:
            if not MOBILE_PATTERN.fullmatch(value or ''):
                raise serializers.ValidationError('手机号必须为 11 位，且以 1 开头')
        return value


class SysLoginLogSerializer(serializers.ModelSerializer):
    """登录日志只读序列化"""

    class Meta:
        model = SysLoginLog
        fields = '__all__'
        read_only_fields = (
            'id', 'user_id', 'user_name', 'login_ip', 'user_agent',
            'status', 'message', 'login_time',
        )
