from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.sys_user_role.models import SysUserRole

SUPER_ADMIN_ROLE_ID = 1


def is_super_admin(user):
    """判断当前登录用户是否绑定了超级管理员角色（role_id=1）"""
    if not getattr(user, 'is_authenticated', False):
        return False
    user_id = getattr(user, 'pk', None)
    if user_id is None:
        return False
    return SysUserRole.objects.filter(
        user_id=user_id, role_id=SUPER_ADMIN_ROLE_ID
    ).exists()


class IsSuperAdmin(BasePermission):
    message = '仅超级管理员可执行该操作'

    def has_permission(self, request, view):
        return is_super_admin(request.user)


class IsSuperAdminOrReadOnly(BasePermission):
    """读接口所有登录用户可用，写接口仅超级管理员可用"""

    message = '仅超级管理员可执行该操作'

    def has_permission(self, request, view):
        # 显式声明该权限类会覆盖全局 IsAuthenticated，这里必须先校验登录态
        if not getattr(request.user, 'is_authenticated', False):
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_super_admin(request.user)
