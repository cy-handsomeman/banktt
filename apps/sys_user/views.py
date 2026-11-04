from django.shortcuts import render
from django.contrib.auth.hashers import check_password
from django.db import transaction
from rest_framework import viewsets, status  # 需要添加 status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response  # 需要添加 Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from apps.sys_user.models import SysUser
from apps.sys_user.serializers import SysUserSerializer
from apps.sys_user.permissions import IsSuperAdmin
from apps.sys_user_role.models import SysUserRole


def sys_user_list(request):
    users = SysUser.objects.all()
    return render(request, 'sys_user.html', {'users': users})


class SysUserViewSet(viewsets.ModelViewSet):
    queryset = SysUser.objects.all().order_by('create_time')
    serializer_class = SysUserSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['user_id', 'user_name', 'mobile', 'pid']
    search_fields = ['user_name', 'mobile', 'pid', 'email', 'address']

    def perform_destroy(self, instance):
        # 不能删除自己，也不能在还绑定角色时直接删除账号
        if instance.pk == self.request.user.pk:
            raise ValidationError({'detail': '不能删除当前登录的账号'})
        role_count = SysUserRole.objects.filter(user_id=instance.user_id).count()
        if role_count:
            raise ValidationError(
                {'detail': f'账号「{instance.user_name}」还绑定了 {role_count} 个角色，请先解除角色绑定'}
            )
        with transaction.atomic():
            instance.delete()
    
    @action(
        detail=False,
        methods=['post'],
        url_path='login',
        permission_classes=[AllowAny],   # 白名单：登录不需要 token
        authentication_classes=[],       # 忽略请求头里可能过期的 token
    )
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
        if user is None or not check_password(password, user.password):
            # 统一提示，避免通过错误信息枚举账号
            return Response(
                {'code': 40101, 'message': '用户名或密码错误', 'data': None},
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