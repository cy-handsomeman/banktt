from django.db import IntegrityError, transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.sys_menu.models import SysMenu
from apps.sys_role.models import SysRole
from apps.sys_role_menu.models import SysRoleMenu
from apps.sys_role_menu.serializers import SysRoleMenuSerializer
from apps.sys_user.permissions import IsSuperAdmin


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class SysRoleMenuViewSet(viewsets.ModelViewSet):
    queryset = SysRoleMenu.objects.all().order_by('role_id', 'menu_id')
    serializer_class = SysRoleMenuSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['role_id', 'menu_id']

    def get_queryset(self):
        queryset = super().get_queryset()
        role_id = self.request.query_params.get('role_id')
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        return queryset

    def create(self, request, *args, **kwargs):
        """单个绑定：重复绑定返回 409，角色/菜单不存在返回 400"""
        role_id = _to_int(request.data.get('role_id'))
        menu_id = _to_int(request.data.get('menu_id'))
        if role_id is None or menu_id is None:
            return Response({'detail': 'role_id 与 menu_id 必须为整数'}, status=status.HTTP_400_BAD_REQUEST)
        if not SysRole.objects.filter(role_id=role_id).exists():
            return Response({'detail': '角色不存在'}, status=status.HTTP_400_BAD_REQUEST)
        if not SysMenu.objects.filter(menu_id=menu_id).exists():
            return Response({'detail': '菜单不存在'}, status=status.HTTP_400_BAD_REQUEST)
        if SysRoleMenu.objects.filter(role_id=role_id, menu_id=menu_id).exists():
            return Response({'detail': '该角色已绑定此菜单'}, status=status.HTTP_409_CONFLICT)
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            # 并发下两个请求同时通过上面的存在性检查，由唯一约束兜底
            return Response({'detail': '该角色已绑定此菜单'}, status=status.HTTP_409_CONFLICT)

    @action(detail=False, methods=['post'], url_path='batch')
    def batch_save(self, request):
        role_id = _to_int(request.data.get('role_id'))
        menu_ids = request.data.get('menu_ids', [])

        if role_id is None:
            return Response({'detail': '角色ID不能为空且必须为整数'}, status=status.HTTP_400_BAD_REQUEST)
        if not SysRole.objects.filter(role_id=role_id).exists():
            return Response({'detail': '角色不存在'}, status=status.HTTP_400_BAD_REQUEST)

        parsed_ids = [_to_int(menu_id) for menu_id in menu_ids]
        if any(menu_id is None for menu_id in parsed_ids):
            return Response({'detail': '菜单ID格式不正确'}, status=status.HTTP_400_BAD_REQUEST)

        existing_ids = set(
            SysMenu.objects.filter(menu_id__in=parsed_ids).values_list('menu_id', flat=True)
        )
        missing_ids = [menu_id for menu_id in parsed_ids if menu_id not in existing_ids]
        if missing_ids:
            return Response(
                {'detail': f'菜单不存在：{missing_ids}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                SysRoleMenu.objects.filter(role_id=role_id).delete()
                SysRoleMenu.objects.bulk_create([
                    SysRoleMenu(role_id=role_id, menu_id=menu_id)
                    for menu_id in dict.fromkeys(parsed_ids)  # 去重，避免重复绑定
                ])
        except IntegrityError:
            # 校验与写入之间菜单被删除等并发情况，统一返回可读错误而不是 500
            return Response(
                {'detail': '角色菜单绑定冲突，请刷新后重试'},
                status=status.HTTP_409_CONFLICT
            )
        return Response({'success': True}, status=status.HTTP_200_OK)
