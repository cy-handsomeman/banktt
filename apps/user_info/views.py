from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.sys_user.permissions import BusinessPermission
from apps.user_info.models import UserInfo
from apps.user_info.serializers import UserSerializer


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """客户资料：查询员只读，管理员与柜员可新增/编辑（不提供删除）"""

    queryset = UserInfo.objects.all().order_by('customer_id')
    serializer_class = UserSerializer
    permission_classes = [BusinessPermission]
    filterset_fields = ['customer_id', 'customer_name', 'pid', 'telephone']
    search_fields = ['customer_name', 'pid', 'telephone', 'address']

    @action(detail=False, methods=['get'], url_path='options')
    def customer_options(self, request):
        """客户下拉选项：只返回编号与姓名，供开卡等场景选择"""
        data = list(
            UserInfo.objects.order_by('customer_id').values('customer_id', 'customer_name')
        )
        return Response(data)
