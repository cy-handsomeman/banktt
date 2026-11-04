from django.db import transaction
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from apps.card_info.models import CardInfo
from apps.sys_user.permissions import BusinessPermission
from apps.user_info.models import UserInfo
from apps.user_info.serializers import UserSerializer


def user_info_list(request):
    return render(request, 'user_info.html')


class UserViewSet(viewsets.ModelViewSet):
    queryset = UserInfo.objects.all().order_by('customer_id')
    serializer_class = UserSerializer
    permission_classes = [BusinessPermission]
    filterset_fields = ['customer_id', 'customer_name', 'pid', 'telephone']
    search_fields = ['customer_name', 'pid', 'telephone', 'address']

    def perform_destroy(self, instance):
        # 客户名下还有银行卡时不允许直接删除，避免外键约束报 500
        card_count = CardInfo.objects.filter(customer_id=instance.customer_id).count()
        if card_count:
            raise ValidationError(
                f'客户「{instance.customer_name}」名下还有 {card_count} 张银行卡，'
                f'请先销卡后再删除客户'
            )
        with transaction.atomic():
            instance.delete()