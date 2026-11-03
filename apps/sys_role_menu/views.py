from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.sys_role_menu.models import SysRoleMenu
from apps.sys_role_menu.serializers import SysRoleMenuSerializer


class SysRoleMenuViewSet(viewsets.ModelViewSet):
    queryset = SysRoleMenu.objects.all()
    serializer_class = SysRoleMenuSerializer
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

        try:
            SysRoleMenu.objects.filter(role_id=role_id).delete()

            for menu_id in menu_ids:
                SysRoleMenu.objects.create(role_id=role_id, menu_id=menu_id)

            return Response({'success': True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
