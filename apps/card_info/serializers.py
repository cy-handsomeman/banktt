import re

from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from apps.card_info.models import CardInfo
from apps.user_info.models import UserInfo

CARD_ID_PATTERN = re.compile(r'^\d{6,20}$')


class CardInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardInfo
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            # 余额与卡状态只能通过交易 / 卡状态动作变动，禁止直接改
            'balance': {'read_only': True},
            'card_status': {'read_only': True},
        }

    def validate(self, attrs):
        """新增时必须携带密码；开户金额只在新增时生效"""
        if self.instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'password': '密码不能为空'})
        if self.instance is None:
            # 开户金额即初始余额
            attrs['balance'] = attrs.get('open_money') or 0
        else:
            # 开户后开户金额不可修改，余额只能由交易产生
            attrs.pop('open_money', None)
            attrs.pop('balance', None)
        return attrs

    def validate_card_id(self, value):
        """卡号格式校验：新建时必须是 6-20 位数字；历史卡号保持原值时不拦截"""
        if self.instance is not None and value == self.instance.card_id:
            return value
        if not CARD_ID_PATTERN.fullmatch(value or ''):
            raise serializers.ValidationError('卡号必须为 6-20 位数字')
        return value

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

    def validate_customer_id(self, value):
        """客户必须已存在"""
        if not UserInfo.objects.filter(customer_id=value).exists():
            raise serializers.ValidationError('客户不存在，请先创建客户')
        return value
