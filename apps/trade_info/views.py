from decimal import Decimal

from django.db import transaction
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from apps.card_info.models import CardInfo
from apps.sys_user.permissions import BusinessPermission
from apps.trade_info.models import TradeInfo
from apps.trade_info.serializers import (
    INFLOW_TRANS_TYPES,
    TRANSFER_IN_TYPE,
    TRANSFER_OUT_TYPE,
    TRANSFER_TRANS_TYPES,
    TradeInfoSerializer,
)


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
    permission_classes = [BusinessPermission]
    filterset_fields = ['trans_type', 'card_id']
    search_fields = ['trans_type', 'card_id', 'remark']

    def perform_create(self, serializer):
        with transaction.atomic():
            trade = serializer.save()
            _change_balance(trade.card_id, _signed_amount(trade))
            # 转账是双边记账：付款方一条转出流水，收款方一条转入流水
            if trade.trans_type == TRANSFER_OUT_TYPE:
                TradeInfo.objects.create(
                    trans_type=TRANSFER_IN_TYPE,
                    card_id=trade.to_card_id,
                    to_card_id=trade.card_id,
                    trans_date=trade.trans_date,
                    trans_money=trade.trans_money,
                    remark=f'转入，来自 {trade.card_id}',
                )
                _change_balance(trade.to_card_id, trade.trans_money)

    def perform_update(self, serializer):
        old_trade = self.get_object()
        if old_trade.trans_type in TRANSFER_TRANS_TYPES:
            raise ValidationError({'detail': '转账流水不支持修改；如需撤销请提交冲正'})
        with transaction.atomic():
            # 先冲销原交易，再按新数据记账
            _change_balance(old_trade.card_id, -_signed_amount(old_trade))
            trade = serializer.save()
            _change_balance(trade.card_id, _signed_amount(trade))

    def perform_destroy(self, instance):
        if instance.trans_type in TRANSFER_TRANS_TYPES:
            raise ValidationError({'detail': '转账流水不支持删除；如需撤销请提交冲正'})
        with transaction.atomic():
            _change_balance(instance.card_id, -_signed_amount(instance))
            instance.delete()
