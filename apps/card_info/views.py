from django.shortcuts import render
from rest_framework import viewsets, status  # 需要添加 status
from rest_framework.response import Response  # 需要添加 Response
from rest_framework.decorators import action
from apps.card_info.models import CardInfo
from apps.card_info.serializers import CardInfoSerializer


def card_info_list(request):
    return render(request, 'card_info.html')


class CardInfoViewSet(viewsets.ModelViewSet):
    queryset = CardInfo.objects.all()
    serializer_class = CardInfoSerializer

    # ↓ 把这段代码放在这里 ↓
    @action(detail=False, methods=['get'], url_path='(?P<cardId>[^/.]+)')
    def get_card_info(self, request, cardId=None):
        """
        获取用户当前角色
        路径为：/api/card_info/{card_id}/
        """
        try:
            card_info = CardInfo.objects.filter(card_id=cardId).first()
            
            if card_info:
                serializer = self.get_serializer(card_info)
                return Response(serializer.data)
            return Response({'message': '未找到银行卡信息'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )