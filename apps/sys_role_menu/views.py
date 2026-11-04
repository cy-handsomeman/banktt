from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.sys_role_menu.models import SysRoleMenu
from apps.sys_role_menu.serializers import SysRoleMenuSerializer
from apps.sys_role.models import SysRole
from apps.sys_menu.models import SysMenu
from apps.sys_user.permissions import IsSuperAdmin


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

    @action(detail=False, methods=['post'], url_path='batch')
    def batch_save(self, request):
        role_id = request.data.get('role_id')
        menu_ids = request.data.get('menu_ids', [])

        if not role_id:
            return Response({'error': '角色ID不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        if not SysRole.objects.filter(role_id=role_id).exists():
            return Response({'error': '角色不存在'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            menu_ids = [int(menu_id) for menu_id in menu_ids]
        except (TypeError, ValueError):
            return Response({'error': '菜单ID格式不正确'}, status=status.HTTP_400_BAD_REQUEST)

        existing_ids = set(
            SysMenu.objects.filter(menu_id__in=menu_ids).values_list('menu_id', flat=True)
        )
        missing_ids = [menu_id for menu_id in menu_ids if menu_id not in existing_ids]
        if missing_ids:
            return Response(
                {'error': f'菜单不存在：{missing_ids}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                SysRoleMenu.objects.filter(role_id=role_id).delete()
                SysRoleMenu.objects.bulk_create([
                    SysRoleMenu(role_id=role_id, menu_id=menu_id)
                    for menu_id in dict.fromkeys(menu_ids)  # 去重，避免重复绑定
                ])
            return Response({'success': True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
