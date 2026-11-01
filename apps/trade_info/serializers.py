from rest_framework import serializers
from apps.trade_info.models import TradeInfo


class TradeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeInfo
        fields = '__all__'
