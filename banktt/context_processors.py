"""模板上下文：把当前登录用户的角色信息注入页面，供模板直接控制只读状态。

页面鉴权依赖 page_token Cookie（refresh token），模板渲染时无法访问 DRF 的
request.user，因此这里自行解析 Cookie 中的 user_id 并查询角色，避免页面按钮
显隐完全依赖前端异步请求。
"""

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.sys_user_role.models import SysUserRole

PAGE_TOKEN_COOKIE = 'page_token'
WRITE_ROLE_IDS = frozenset({1, 2})


def current_user_roles(request):
    token = request.COOKIES.get(PAGE_TOKEN_COOKIE)
    if not token:
        return {'current_role_ids': [], 'can_write_business': False, 'is_super_admin_page': False}
    try:
        validated = RefreshToken(token)
    except TokenError:
        return {'current_role_ids': [], 'can_write_business': False, 'is_super_admin_page': False}
    user_id = validated.get('user_id')
    if not user_id:
        return {'current_role_ids': [], 'can_write_business': False, 'is_super_admin_page': False}
    role_ids = list(
        SysUserRole.objects.filter(user_id=user_id).values_list('role_id', flat=True)
    )
    roles = set(role_ids)
    return {
        'current_role_ids': role_ids,
        'can_write_business': bool(roles & WRITE_ROLE_IDS),
        'is_super_admin_page': 1 in roles,
    }
