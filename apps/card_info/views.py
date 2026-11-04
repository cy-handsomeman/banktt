from django.db import transaction
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from apps.card_info.models import CardInfo
from apps.card_info.serializers import CardInfoSerializer
from apps.sys_user.permissions import BusinessPermission
from apps.trade_info.models import TradeInfo


def card_info_list(request):
    return render(request, 'card_info.html')


class CardInfoViewSet(viewsets.ModelViewSet):
    queryset = CardInfo.objects.all().order_by('card_id')
    serializer_class = CardInfoSerializer
    permission_classes = [BusinessPermission]
    filterset_fields = ['card_id', 'cur_type', 'customer_id']
    search_fields = ['card_id', 'cur_type']

    def perform_destroy(self, instance):
        # 卡上有交易流水时不允许物理删除，避免外键约束报 500
        trade_count = TradeInfo.objects.filter(card_id=instance.card_id).count()
        if trade_count:
            raise ValidationError(
                f'银行卡「{instance.card_id}」存在 {trade_count} 条交易流水，不能删除'
            )
        with transaction.atomic():
            instance.delete()