from rest_framework import serializers

from apps.card_info.models import CardInfo
from apps.trade_info.models import TradeInfo

# 客户端可提交的交易类型；转账落库时会拆成「转账转出 / 转账转入」两条流水
ALLOWED_TRANS_TYPES = ('存款', '取款', '转账', '消费', '还款')
TRANSFER_TYPE = '转账'
TRANSFER_OUT_TYPE = '转账转出'
TRANSFER_IN_TYPE = '转账转入'
INFLOW_TRANS_TYPES = ('存款', '还款', TRANSFER_IN_TYPE)

CARD_STATUS_NORMAL = '正常'


def _ensure_card_available(card_id, field_name):
    """银行卡必须存在且状态为正常，挂失/销户卡禁止参与交易"""
    card = CardInfo.objects.filter(card_id=card_id).only('card_status').first()
    if card is None:
        raise serializers.ValidationError({field_name: '银行卡不存在'})
    if (card.card_status or CARD_STATUS_NORMAL) != CARD_STATUS_NORMAL:
        raise serializers.ValidationError(
            {field_name: f'银行卡状态为「{card.card_status}」，不能进行交易'}
        )


class TradeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeInfo
        fields = '__all__'
        extra_kwargs = {
            # 交易日期由后端生成，余额快照/冲正标记由后端维护
            'trans_date': {'read_only': True},
            'balance_after': {'read_only': True},
            'is_reversed': {'read_only': True},
            'pair_tid': {'read_only': True},
        }

    def validate_trans_type(self, value):
        """交易类型必须为系统支持的取值；历史转账流水保持原值时不拦截"""
        if self.instance is not None and value == self.instance.trans_type:
            return value
        if value not in ALLOWED_TRANS_TYPES:
            raise serializers.ValidationError(f'交易类型必须为：{"、".join(ALLOWED_TRANS_TYPES)}')
        return value

    def validate_card_id(self, value):
        """银行卡必须已存在且状态正常"""
        _ensure_card_available(value, 'card_id')
        return value

    def validate_trans_money(self, value):
        """交易金额必须大于 0"""
        if value <= 0:
            raise serializers.ValidationError('交易金额必须大于 0')
        return value

    def validate(self, attrs):
        """转账必须指定收款卡，且不允许与本卡相同"""
        trans_type = attrs.get('trans_type', getattr(self.instance, 'trans_type', None))
        card_id = attrs.get('card_id', getattr(self.instance, 'card_id', None))
        to_card_id = attrs.get('to_card_id', getattr(self.instance, 'to_card_id', None))

        if trans_type == TRANSFER_TYPE:
            if not to_card_id:
                raise serializers.ValidationError({'to_card_id': '转账必须填写收款卡号'})
            if to_card_id == card_id:
                raise serializers.ValidationError({'to_card_id': '收款卡号不能与付款卡号相同'})
            _ensure_card_available(to_card_id, 'to_card_id')
            # 落库时转成转出流水，另一条转入流水由视图层生成
            attrs['trans_type'] = TRANSFER_OUT_TYPE
        elif to_card_id:
            raise serializers.ValidationError({'to_card_id': '仅转账交易可填写收款卡号'})

        return attrs
