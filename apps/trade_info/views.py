from django.shortcuts import render
from rest_framework import viewsets
from apps.trade_info.models import TradeInfo
from apps.trade_info.serializers import TradeInfoSerializer


def trade_info_list(request):
    return render(request, 'trade_info.html')


class TradeInfoViewSet(viewsets.ModelViewSet):
    queryset = TradeInfo.objects.all()
    serializer_class = TradeInfoSerializer
    filterset_fields = ['trans_type', 'card_id']
    search_fields = ['trans_type', 'card_id', 'remark']
