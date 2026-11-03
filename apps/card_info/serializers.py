from rest_framework import serializers
from apps.card_info.models import CardInfo


class CardInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardInfo
        fields = '__all__'

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
