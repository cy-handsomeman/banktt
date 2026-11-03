from django.shortcuts import render
from django.contrib.auth.hashers import check_password
from rest_framework import viewsets, status  # 需要添加 status
from rest_framework.response import Response  # 需要添加 Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from apps.sys_user.models import SysUser
from apps.sys_user.serializers import SysUserSerializer


def sys_user_list(request):
    users = SysUser.objects.all()
    return render(request, 'sys_user.html', {'users': users})


class SysUserViewSet(viewsets.ModelViewSet):
    queryset = SysUser.objects.all().order_by('create_time')
    serializer_class = SysUserSerializer
    filterset_fields = ['user_id', 'user_name', 'mobile', 'pid']
    search_fields = ['user_name', 'mobile', 'pid', 'email', 'address']
    
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """登录接口：校验通过后签发 access / refresh token"""
        user_name = request.data.get('userName')
        password = request.data.get('password')

        if not user_name or str(user_name).strip() == '':
            return Response(
                {'code': 40001, 'message': '用户名不能为空', 'data': None},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not password:
            return Response(
                {'code': 40002, 'message': '密码不能为空', 'data': None},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = SysUser.objects.filter(user_name=user_name).first()
        if user is None:
            return Response(
                {'code': 40101, 'message': '用户名不存在', 'data': None},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if not check_password(password, user.password):
            return Response(
                {'code': 40102, 'message': '密码错误', 'data': None},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'code': 0,
                'message': '登录成功',
                'data': {
                    'user_id': user.user_id,
                    'user_name': user.user_name,
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
            },
            status=status.HTTP_200_OK
        )