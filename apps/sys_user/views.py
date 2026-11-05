from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status  # 需要添加 status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response  # 需要添加 Response
from rest_framework.decorators import action
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from apps.sys_user.models import SysLoginLog, SysUser
from apps.sys_user.serializers import SysLoginLogSerializer, SysUserSerializer
from apps.sys_user.permissions import IsSuperAdmin
from apps.sys_user_role.models import SysUserRole
from banktt.middleware import PAGE_TOKEN_COOKIE


def login_log_list(request):
    return render(request, 'sys_login_log.html')


def _client_ip(request):
    """仅当请求来自受信代理时才采用 X-Forwarded-For，避免客户端伪造来源 IP"""
    remote_addr = request.META.get('REMOTE_ADDR') or ''
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded and remote_addr in getattr(settings, 'TRUSTED_PROXY_IPS', ()):
        return forwarded.split(',')[0].strip()
    return remote_addr


def _write_login_log(request, user, user_name, success, message):
    """记录登录结果；写日志失败不能影响登录本身"""
    try:
        SysLoginLog.objects.create(
            user_id=getattr(user, 'user_id', None),
            user_name=(user_name or '')[:100],
            login_ip=_client_ip(request)[:64],
            user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:255],
            status='成功' if success else '失败',
            message=message,
            login_time=timezone.now(),
        )
    except Exception:
        pass


class SysLoginLogViewSet(ReadOnlyModelViewSet):
    """登录日志查询（只读，仅超级管理员可见）"""

    queryset = SysLoginLog.objects.all().order_by('-id')
    serializer_class = SysLoginLogSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['user_id', 'user_name', 'status']
    search_fields = ['user_name', 'login_ip', 'message']


class SysUserViewSet(viewsets.ModelViewSet):
    queryset = SysUser.objects.all().order_by('create_time')
    serializer_class = SysUserSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['user_id', 'user_name', 'mobile', 'pid']
    search_fields = ['user_name', 'mobile', 'pid', 'email', 'address']
    # 仅在 login action 使用 ScopedRateThrottle 时生效
    throttle_scope = 'login'

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
        throttle_classes=[ScopedRateThrottle],  # 登录接口单独限流，防暴力破解
    )
    def login(self, request):
        """登录接口：校验通过后签发 access / refresh token，并记录登录日志"""
        user_name = (request.data.get('userName') or '').strip()
        password = request.data.get('password')

        if not user_name:
            _write_login_log(request, None, user_name, False, '用户名不能为空')
            return Response(
                {'code': 40001, 'message': '用户名不能为空', 'data': None},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not password:
            _write_login_log(request, None, user_name, False, '密码不能为空')
            return Response(
                {'code': 40002, 'message': '密码不能为空', 'data': None},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = SysUser.objects.filter(user_name=user_name).first()
        if user is None or not check_password(password, user.password):
            # 统一提示，避免通过错误信息枚举账号
            _write_login_log(request, user, user_name, False, '用户名或密码错误')
            return Response(
                {'code': 40101, 'message': '用户名或密码错误', 'data': None},
                status=status.HTTP_401_UNAUTHORIZED
            )

        _write_login_log(request, user, user_name, True, '登录成功')
        refresh = RefreshToken.for_user(user)
        response = Response(
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
        # 页面鉴权 Cookie 由服务端下发并标记 HttpOnly，前端无法读取或篡改
        response.set_cookie(
            PAGE_TOKEN_COOKIE,
            str(refresh),
            max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
            path='/',
            httponly=True,
            samesite='Lax',
            secure=request.is_secure(),
        )
        return response

    @action(
        detail=False,
        methods=['post'],
        url_path='logout',
        permission_classes=[AllowAny],   # 退出登录不要求 token 仍然有效
        authentication_classes=[],
    )
    def logout(self, request):
        """退出登录：清除服务端下发的 HttpOnly 页面鉴权 Cookie"""
        response = Response({'detail': '已退出登录'}, status=status.HTTP_200_OK)
        response.delete_cookie(PAGE_TOKEN_COOKIE, path='/')
        return response