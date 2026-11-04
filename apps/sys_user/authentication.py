from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings

from apps.sys_user.models import SysUser


class SysUserJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """让 drf-spectacular 识别自定义 JWT 认证类，避免 schema 生成警告"""

    target_class = 'apps.sys_user.authentication.SysUserJWTAuthentication'
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }


class SysUserPrincipal:
    """把 sys_user 实例包装成 DRF 认可的用户主体（DRF 要求 is_authenticated 为 True）"""

    def __init__(self, sys_user):
        self._sys_user = sys_user
        self.pk = sys_user.user_id
        self.id = sys_user.user_id

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        return True

    def __getattr__(self, item):
        if item == '_sys_user':
            raise AttributeError(item)
        return getattr(self._sys_user, item)

    def __str__(self):
        return self._sys_user.user_name


class SysUserJWTAuthentication(JWTAuthentication):
    """适配 sys_user 表的 JWT 认证：按 token 中的 user_id 查询 sys_user"""

    def get_user(self, validated_token):
        user_id = validated_token.get(api_settings.USER_ID_CLAIM)
        if user_id is None:
            raise AuthenticationFailed('Token 中缺少用户标识', code='token_no_user_id')
        try:
            sys_user = SysUser.objects.get(user_id=user_id)
        except SysUser.DoesNotExist:
            raise AuthenticationFailed('用户不存在或已被删除', code='user_not_found')
        return SysUserPrincipal(sys_user)
