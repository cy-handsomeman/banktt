from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.sys_role_menu.models import SysRoleMenu
from apps.sys_role_menu.serializers import SysRoleMenuSerializer


class SysRoleMenuViewSet(viewsets.ModelViewSet):
    queryset = SysRoleMenu.objects.all()
    serializer_class = SysRoleMenuSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        role_id = self.request.query_params.get('role_id')
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        return queryset

    @method_decorator(csrf_exempt)
    @action(detail=False, methods=['post'], url_path='batch')
    def batch_save(self, request):
        print("请求数据:", request.data)
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
            print("保存失败:", str(e))
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
