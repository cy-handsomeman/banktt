from rest_framework import serializers
from apps.card_info.models import CardInfo


class CardInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardInfo
        fields = '__all__'
