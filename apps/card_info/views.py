from decimal import Decimal

from django.db import transaction
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.card_info.models import CardInfo
from apps.card_info.serializers import CardInfoSerializer
from apps.sys_user.permissions import BusinessPermission, is_manager_or_admin
from apps.trade_info.models import TradeInfo

CARD_STATUS_NORMAL = '正常'
CARD_STATUS_LOST = '挂失'
CARD_STATUS_CLOSED = '销户'


def card_info_list(request):
    return render(request, 'card_info.html')


class CardInfoViewSet(viewsets.ModelViewSet):
    queryset = CardInfo.objects.all().order_by('card_id')
    serializer_class = CardInfoSerializer
    permission_classes = [BusinessPermission]
    filterset_fields = ['card_id', 'cur_type', 'customer_id', 'card_status']
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

    def _change_status(self, request, pk, target_status):
        """在事务内锁卡并校验状态流转是否合法"""
        with transaction.atomic():
            card = CardInfo.objects.select_for_update().filter(pk=pk).first()
            if card is None:
                raise ValidationError({'detail': '银行卡不存在'})

            current = card.card_status or CARD_STATUS_NORMAL
            if current == CARD_STATUS_CLOSED:
                raise ValidationError({'detail': '已销户的银行卡不能变更状态'})

            if target_status == CARD_STATUS_LOST and current != CARD_STATUS_NORMAL:
                raise ValidationError({'detail': '只有正常状态的银行卡可以挂失'})
            if target_status == CARD_STATUS_NORMAL and current != CARD_STATUS_LOST:
                raise ValidationError({'detail': '只有挂失状态的银行卡可以解挂'})
            if target_status == CARD_STATUS_CLOSED:
                if not is_manager_or_admin(request.user):
                    raise PermissionDenied('仅超级管理员或大堂经理可办理销卡')
                if (card.balance or Decimal('0')) != Decimal('0'):
                    raise ValidationError(
                        {'detail': f'卡内余额为 {card.balance}，请先结清余额再销卡'}
                    )

            card.card_status = target_status
            card.save(update_fields=['card_status'])
            return card

    @action(detail=True, methods=['post'], url_path='report-loss')
    def report_loss(self, request, pk=None):
        """挂失：正常 -> 挂失"""
        card = self._change_status(request, pk, CARD_STATUS_LOST)
        return Response({'card_id': card.card_id, 'card_status': card.card_status})

    @action(detail=True, methods=['post'], url_path='unlock')
    def unlock(self, request, pk=None):
        """解挂：挂失 -> 正常"""
        card = self._change_status(request, pk, CARD_STATUS_NORMAL)
        return Response({'card_id': card.card_id, 'card_status': card.card_status})

    @action(detail=True, methods=['post'], url_path='close')
    def close(self, request, pk=None):
        """销卡：余额为 0 时可将正常/挂失卡置为销户"""
        card = self._change_status(request, pk, CARD_STATUS_CLOSED)
        return Response({'card_id': card.card_id, 'card_status': card.card_status})
