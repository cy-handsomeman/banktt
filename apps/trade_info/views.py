from decimal import Decimal

from django.db import transaction
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from apps.card_info.models import CardInfo
from apps.trade_info.models import TradeInfo
from apps.trade_info.serializers import INFLOW_TRANS_TYPES, TradeInfoSerializer


def trade_info_list(request):
    return render(request, 'trade_info.html')


def _signed_amount(trade):
    """入账为正、出账为负"""
    if trade.trans_type in INFLOW_TRANS_TYPES:
        return trade.trans_money
    return -trade.trans_money


def _change_balance(card_id, delta):
    """在事务内锁行并更新余额，余额不足时抛出校验错误"""
    card = CardInfo.objects.select_for_update().filter(card_id=card_id).first()
    if card is None:
        raise ValidationError({'card_id': '银行卡不存在'})
    new_balance = (card.balance or Decimal('0')) + delta
    if new_balance < 0:
        raise ValidationError({'trans_money': '银行卡余额不足'})
    card.balance = new_balance
    card.save(update_fields=['balance'])


class TradeInfoViewSet(viewsets.ModelViewSet):
    queryset = TradeInfo.objects.all().order_by('-tid')
    serializer_class = TradeInfoSerializer
    filterset_fields = ['trans_type', 'card_id']
    search_fields = ['trans_type', 'card_id', 'remark']

    def perform_create(self, serializer):
        with transaction.atomic():
            trade = serializer.save()
            _change_balance(trade.card_id, _signed_amount(trade))

    def perform_update(self, serializer):
        with transaction.atomic():
            old_trade = self.get_object()
            # 先冲销原交易，再按新数据记账
            _change_balance(old_trade.card_id, -_signed_amount(old_trade))
            trade = serializer.save()
            _change_balance(trade.card_id, _signed_amount(trade))

    def perform_destroy(self, instance):
        with transaction.atomic():
            _change_balance(instance.card_id, -_signed_amount(instance))
            instance.delete()
