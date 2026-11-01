from rest_framework import serializers 
from apps.user_info.models import UserInfo 

class UserSerializer(serializers.ModelSerializer):
    """用户表序列化"""
    class Meta:
        model = UserInfo
        fields = '__all__'