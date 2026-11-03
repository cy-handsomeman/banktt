from django.shortcuts import render
from rest_framework import viewsets
from apps.card_info.models import CardInfo
from apps.card_info.serializers import CardInfoSerializer


def card_info_list(request):
    return render(request, 'card_info.html')


class CardInfoViewSet(viewsets.ModelViewSet):
    queryset = CardInfo.objects.all().order_by('card_id')
    serializer_class = CardInfoSerializer
    filterset_fields = ['card_id', 'cur_type', 'customer_id']
    search_fields = ['card_id', 'cur_type']