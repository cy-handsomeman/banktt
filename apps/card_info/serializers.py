from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from apps.card_info.models import CardInfo


class CardInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardInfo
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

    def validate_open_money(self, value):
        """开户金额不能为负数"""
        if value < 0:
            raise serializers.ValidationError('开户金额不能为负数')
        return value

    def validate_balance(self, value):
        """余额不能为负数"""
        if value < 0:
            raise serializers.ValidationError('余额不能为负数')
        return value
