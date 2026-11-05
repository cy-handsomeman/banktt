"""页面级鉴权：为只能登录后访问的 HTML 页面提供统一入口校验。

背景：前端 token 保存在 sessionStorage，浏览器直接打开页面时不会携带
Authorization 头，因此页面层无法复用 DRF 的 JWT 认证。登录成功后前端会把
refresh token 同步写入 page_token Cookie，本中间件只负责校验这个 Cookie 是否
是合法且未过期的 refresh token，并对应用户仍然存在；真正的业务数据权限仍由
各 API 的权限类负责。
"""

from django.http import HttpResponseRedirect
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.sys_user.models import SysUser

# 需要登录后才能访问的页面路径（登录页、接口文档、静态资源不在其中）
PROTECTED_PAGE_PATHS = frozenset({
    '/',
    '/dashboard/',
    '/user/',
    '/card/',
    '/trade/',
    '/transactions/',
    '/sys_user/',
    '/role/',
    '/login_log/',
})

PAGE_TOKEN_COOKIE = 'page_token'


class PageAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in PROTECTED_PAGE_PATHS and not self._has_valid_page_token(request):
            return HttpResponseRedirect('/login/')
        return self.get_response(request)

    @staticmethod
    def _has_valid_page_token(request):
        token = request.COOKIES.get(PAGE_TOKEN_COOKIE)
        if not token:
            return False
        try:
            validated = RefreshToken(token)
        except TokenError:
            return False
        user_id = validated.get('user_id')
        if not user_id:
            return False
        return SysUser.objects.filter(user_id=user_id).exists()
