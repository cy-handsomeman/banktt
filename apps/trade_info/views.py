from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.card_info.models import CardInfo
from apps.sys_user.permissions import BusinessPermission, is_manager_or_admin
from apps.trade_info.models import TradeInfo
from apps.trade_info.serializers import (
    INFLOW_TRANS_TYPES,
    REVERSAL_TYPE,
    TRANSFER_IN_TYPE,
    TRANSFER_OUT_TYPE,
    TRANSFER_TRANS_TYPES,
    TradeInfoSerializer,
)


def _signed_amount(trade):
    """入账为正、出账为负"""
    if trade.trans_type in INFLOW_TRANS_TYPES:
        return trade.trans_money
    return -trade.trans_money


def _change_balance(card_id, delta):
    """在事务内锁行并更新余额，返回变动后余额；余额不足时抛出校验错误"""
    card = CardInfo.objects.select_for_update().filter(card_id=card_id).first()
    if card is None:
        raise ValidationError({'card_id': '银行卡不存在'})
    new_balance = (card.balance or Decimal('0')) + delta
    if new_balance < 0:
        raise ValidationError({'trans_money': '银行卡余额不足'})
    card.balance = new_balance
    card.save(update_fields=['balance'])
    return new_balance


class TradeInfoViewSet(viewsets.ModelViewSet):
    queryset = TradeInfo.objects.all().order_by('-tid')
    serializer_class = TradeInfoSerializer
    permission_classes = [BusinessPermission]
    filterset_fields = ['trans_type', 'card_id', 'is_reversed']
    search_fields = ['trans_type', 'card_id', 'remark']

    def perform_create(self, serializer):
        with transaction.atomic():
            # 交易日期统一由后端生成，避免客户端伪造或时区不一致
            trade = serializer.save(trans_date=timezone.now())
            trade.balance_after = _change_balance(trade.card_id, _signed_amount(trade))
            trade.save(update_fields=['balance_after'])

            # 转账是双边记账：付款方一条转出流水，收款方一条转入流水
            if trade.trans_type == TRANSFER_OUT_TYPE:
                inbound_balance = _change_balance(trade.to_card_id, trade.trans_money)
                counterpart = TradeInfo.objects.create(
                    trans_type=TRANSFER_IN_TYPE,
                    card_id=trade.to_card_id,
                    to_card_id=trade.card_id,
                    trans_date=trade.trans_date,
                    trans_money=trade.trans_money,
                    balance_after=inbound_balance,
                    remark=f'转入，来自 {trade.card_id}',
                )
                trade.pair_tid = counterpart.tid
                counterpart.pair_tid = trade.tid
                trade.save(update_fields=['pair_tid'])
                counterpart.save(update_fields=['pair_tid'])

    def perform_update(self, serializer):
        old_trade = self.get_object()
        if old_trade.trans_type in TRANSFER_TRANS_TYPES:
            raise ValidationError({'detail': '转账流水不支持修改；如需撤销请提交冲正'})
        if old_trade.is_reversed:
            raise ValidationError({'detail': '已冲正的交易不支持修改'})
        if old_trade.trans_type == REVERSAL_TYPE:
            raise ValidationError({'detail': '冲正流水不支持修改'})
        with transaction.atomic():
            # 先冲销原交易，再按新数据记账
            _change_balance(old_trade.card_id, -_signed_amount(old_trade))
            trade = serializer.save()
            trade.balance_after = _change_balance(trade.card_id, _signed_amount(trade))
            trade.save(update_fields=['balance_after'])

    def perform_destroy(self, instance):
        if instance.trans_type in TRANSFER_TRANS_TYPES:
            raise ValidationError({'detail': '转账流水不支持删除；如需撤销请提交冲正'})
        if instance.trans_type == REVERSAL_TYPE:
            raise ValidationError({'detail': '冲正流水不支持删除'})
        if instance.is_reversed:
            raise ValidationError({'detail': '已冲正的交易不支持删除'})
        with transaction.atomic():
            _change_balance(instance.card_id, -_signed_amount(instance))
            instance.delete()

    @action(detail=True, methods=['post'], url_path='reverse')
    def reverse(self, request, pk=None):
        """交易冲正：生成反向流水并把原交易标记为已冲正（转账会成对冲正）"""
        if not is_manager_or_admin(request.user):
            raise PermissionDenied('仅超级管理员或大堂经理可提交冲正')

        with transaction.atomic():
            trade = TradeInfo.objects.select_for_update().filter(pk=pk).first()
            if trade is None:
                raise ValidationError({'detail': '交易不存在'})
            if trade.trans_type == REVERSAL_TYPE:
                raise ValidationError({'detail': '冲正流水不能再冲正'})
            if trade.is_reversed:
                raise ValidationError({'detail': '该交易已冲正，请勿重复提交'})

            legs = [trade]
            pair = None
            if trade.pair_tid:
                pair = TradeInfo.objects.select_for_update().filter(pk=trade.pair_tid).first()
            elif trade.trans_type in TRANSFER_TRANS_TYPES and trade.to_card_id:
                # 兼容历史转账流水（没有 pair_tid）：按双方卡号、金额、时间定位配对流水
                pair_type = (
                    TRANSFER_IN_TYPE if trade.trans_type == TRANSFER_OUT_TYPE
                    else TRANSFER_OUT_TYPE
                )
                pair = TradeInfo.objects.select_for_update().filter(
                    trans_type=pair_type,
                    card_id=trade.to_card_id,
                    to_card_id=trade.card_id,
                    trans_money=trade.trans_money,
                    trans_date=trade.trans_date,
                    is_reversed=False,
                ).first()
            if pair is not None:
                if pair.is_reversed:
                    raise ValidationError({'detail': '配对的转账流水已冲正'})
                legs.append(pair)

            reversal_trades = []
            for leg in legs:
                new_balance = _change_balance(leg.card_id, -_signed_amount(leg))
                reversal = TradeInfo.objects.create(
                    trans_type=REVERSAL_TYPE,
                    card_id=leg.card_id,
                    to_card_id=None,
                    trans_date=timezone.now(),
                    trans_money=leg.trans_money,
                    balance_after=new_balance,
                    remark=f'冲正原交易 #{leg.tid}',
                )
                leg.is_reversed = True
                leg.save(update_fields=['is_reversed'])
                reversal_trades.append(reversal)

            if len(reversal_trades) == 2:
                reversal_trades[0].pair_tid = reversal_trades[1].tid
                reversal_trades[1].pair_tid = reversal_trades[0].tid
                for reversal in reversal_trades:
                    reversal.save(update_fields=['pair_tid'])

            return Response({
                'message': '冲正成功',
                'reversed_tids': [leg.tid for leg in legs],
                'reversal_tids': [reversal.tid for reversal in reversal_trades],
            })
