from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.card_info.models import CardInfo
from apps.trade_info.models import TradeInfo
from apps.user_info.models import UserInfo

CARD_STATUS_NORMAL = '正常'
CARD_STATUS_CLOSED = '销户'
TRANSFER_IN_TYPE = '转账转入'


def dashboard_page(request):
    return render(request, 'dashboard.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    """运营总览：今日交易、客户/银行卡总量、近 7 日趋势与最新流水"""
    today = timezone.localdate()
    today_trades = TradeInfo.objects.filter(trans_date__date=today)

    today_trade_count = today_trades.count()
    # 转账是双边记账，排除转入流水避免金额重复计算
    today_amount = (
        today_trades.exclude(trans_type=TRANSFER_IN_TYPE)
        .aggregate(total=Sum('trans_money'))['total']
        or Decimal('0')
    )

    card_count = CardInfo.objects.count()
    card_normal_count = CardInfo.objects.filter(card_status=CARD_STATUS_NORMAL).count()
    card_closed_count = CardInfo.objects.filter(card_status=CARD_STATUS_CLOSED).count()

    trend = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        trend.append({
            'date': day.strftime('%m-%d'),
            'count': TradeInfo.objects.filter(trans_date__date=day).count(),
        })

    latest_trades = []
    for trade in TradeInfo.objects.order_by('-tid')[:10]:
        latest_trades.append({
            'tid': trade.tid,
            'trans_type': trade.trans_type,
            'card_id': trade.card_id,
            'to_card_id': trade.to_card_id,
            'trans_money': str(trade.trans_money),
            'trans_date': timezone.localtime(trade.trans_date).strftime('%Y-%m-%d %H:%M:%S'),
            'balance_after': str(trade.balance_after) if trade.balance_after is not None else None,
            'remark': trade.remark,
        })

    return Response({
        'today_trade_count': today_trade_count,
        'today_trade_amount': str(today_amount),
        'customer_count': UserInfo.objects.count(),
        'card_count': card_count,
        'card_normal_count': card_normal_count,
        'card_closed_count': card_closed_count,
        'trend': trend,
        'latest_trades': latest_trades,
    })
