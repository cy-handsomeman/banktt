from rest_framework import mixins, viewsets

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
