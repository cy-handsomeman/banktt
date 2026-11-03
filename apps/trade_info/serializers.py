from rest_framework import serializers
from apps.trade_info.models import TradeInfo


class TradeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeInfo
        fields = '__all__'

    def validate_trans_money(self, value):
        """交易金额不能为负数"""
        if value < 0:
            raise serializers.ValidationError('交易金额不能为负数')
        return value
