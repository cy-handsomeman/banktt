from rest_framework import serializers 
from apps.user_info.models import UserInfo 

class UserSerializer(serializers.ModelSerializer):
    """用户表序列化"""
    class Meta:
        model = UserInfo
        fields = '__all__'

    def validate_pid(self, value):
        """身份证号唯一校验：新增与编辑时都排除自身"""
        queryset = UserInfo.objects.filter(pid=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('该身份证号已存在，请勿重复录入')
        return value