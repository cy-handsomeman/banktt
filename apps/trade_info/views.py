import random
import time
from decimal import Decimal

import django_filters
from django.db import OperationalError, transaction
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError

from apps.card_info.models import CardInfo
from apps.sys_user.permissions import BusinessPermission
from apps.trade_info.models import TradeInfo
from apps.trade_info.serializers import (
    INFLOW_TRANS_TYPES,
    TRANSFER_IN_TYPE,
    TRANSFER_OUT_TYPE,
    TRANSFER_TYPE,
    TradeInfoSerializer,
)

# MySQL 死锁错误码：InnoDB 主动回滚事务后，整段重做是安全的
DEADLOCK_ERROR_CODE = 1213
DEADLOCK_MAX_ATTEMPTS = 3


def _signed_amount(trade):
    """入账为正、出账为负"""
    if trade.trans_type in INFLOW_TRANS_TYPES:
        return trade.trans_money
    return -trade.trans_money


def _is_deadlock(exc):
    args = getattr(exc, 'args', ())
    return bool(args) and args[0] == DEADLOCK_ERROR_CODE


def _retry_on_deadlock(func):
    """整段事务重试：死锁时事务已被回滚，重做不会留下半截数据"""
    for attempt in range(1, DEADLOCK_MAX_ATTEMPTS + 1):
        try:
            return func()
        except OperationalError as exc:
            if not _is_deadlock(exc) or attempt == DEADLOCK_MAX_ATTEMPTS:
                raise
            time.sleep(random.uniform(0.01, 0.05) * attempt)


def _lock_cards(card_ids):
    """按卡号升序加行锁：所有事务的加锁顺序一致，避免 ABBA 环形等待"""
    for card_id in sorted({card_id for card_id in card_ids if card_id}):
        CardInfo.objects.select_for_update().filter(card_id=card_id).first()


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


class TradeInfoFilter(django_filters.FilterSet):
    """交易流水筛选：卡号、类型、交易日期范围"""

    start_date = django_filters.DateFilter(field_name='trans_date', lookup_expr='date__gte')
    end_date = django_filters.DateFilter(field_name='trans_date', lookup_expr='date__lte')

    class Meta:
        model = TradeInfo
        fields = ['trans_type', 'card_id']


class TradeInfoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """交易流水：只读查询 + 新增（存款/取款/转账），不提供修改、删除与冲正"""

    queryset = TradeInfo.objects.all().order_by('-tid')
    serializer_class = TradeInfoSerializer
    permission_classes = [BusinessPermission]
    filterset_class = TradeInfoFilter
    search_fields = ['trans_type', 'card_id', 'remark']

    def perform_create(self, serializer):
        validated = serializer.validated_data
        card_ids = [validated.get('card_id'), validated.get('to_card_id')]

        def _create():
            # 重试前清空上次失败时挂上的实例，否则第二次 save() 会走 update 而不是 create
            serializer.instance = None
            with transaction.atomic():
                # 先按固定顺序锁定全部涉及的卡，再记账
                _lock_cards(card_ids)
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

        _retry_on_deadlock(_create)
