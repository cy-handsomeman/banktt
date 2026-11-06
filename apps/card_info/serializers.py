import random
import string

from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from rest_framework import serializers

from apps.card_info.models import CardInfo
from apps.user_info.models import UserInfo

CARD_BIN = '622202'
CARD_ID_LENGTH = 16
CARD_ID_ATTEMPTS = 5


def generate_card_id():
    """生成 16 位卡号：固定卡 BIN + 随机数字，保证视觉上不可猜测"""
    suffix_length = CARD_ID_LENGTH - len(CARD_BIN)
    return CARD_BIN + ''.join(random.choices(string.digits, k=suffix_length))


class CardInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardInfo
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            # 卡号由系统自动生成，前端不可指定
            'card_id': {'read_only': True},
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
            # 卡归属客户不可变更，避免把卡"过户"到其他客户
            customer_id = attrs.get('customer_id')
            if customer_id is not None and customer_id != self.instance.customer_id:
                raise serializers.ValidationError({'customer_id': '银行卡归属客户不可修改'})
            attrs.pop('customer_id', None)
        return attrs

    def create(self, validated_data):
        """由系统生成唯一卡号；极端并发下主键冲突则重试"""
        for _ in range(CARD_ID_ATTEMPTS):
            card_id = generate_card_id()
            if CardInfo.objects.filter(card_id=card_id).exists():
                continue
            validated_data['card_id'] = card_id
            try:
                return super().create(validated_data)
            except IntegrityError:
                continue
        raise serializers.ValidationError({'card_id': '卡号生成冲突，请重试'})

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
