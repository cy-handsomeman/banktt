from rest_framework import serializers

from apps.card_info.models import CardInfo
from apps.trade_info.models import TradeInfo

# 业务允许的交易类型；前两种为入账，其余为出账
ALLOWED_TRANS_TYPES = ('存款', '取款', '转账', '消费', '还款')
INFLOW_TRANS_TYPES = ('存款', '还款')


class TradeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeInfo
        fields = '__all__'

    def validate_trans_type(self, value):
        """交易类型必须为系统支持的取值"""
        if value not in ALLOWED_TRANS_TYPES:
            raise serializers.ValidationError(f'交易类型必须为：{"、".join(ALLOWED_TRANS_TYPES)}')
        return value

    def validate_card_id(self, value):
        """银行卡必须已存在"""
        if not CardInfo.objects.filter(card_id=value).exists():
            raise serializers.ValidationError('银行卡不存在')
        return value

    def validate_trans_money(self, value):
        """交易金额必须大于 0"""
        if value <= 0:
            raise serializers.ValidationError('交易金额必须大于 0')
        return value
