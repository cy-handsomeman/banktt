from django.conf import settings
from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.sys_user_role.models import SysUserRole

# 角色 ID 从配置读取，避免在代码里散落魔法数字
SUPER_ADMIN_ROLE_ID = getattr(settings, 'SUPER_ADMIN_ROLE_ID', 1)
MANAGER_ROLE_ID = getattr(settings, 'MANAGER_ROLE_ID', 2)
TELLER_ROLE_ID = getattr(settings, 'TELLER_ROLE_ID', 3)


def user_role_ids(user):
    """返回当前登录用户拥有的角色 ID 列表"""
    if not getattr(user, 'is_authenticated', False):
        return []
    user_id = getattr(user, 'pk', None)
    if user_id is None:
        return []
    return list(
        SysUserRole.objects.filter(user_id=user_id).values_list('role_id', flat=True)
    )


def has_any_role(user):
    return bool(user_role_ids(user))


def is_super_admin(user):
    """判断当前登录用户是否绑定了超级管理员角色"""
    return SUPER_ADMIN_ROLE_ID in user_role_ids(user)


def is_manager_or_admin(user):
    """超级管理员或大堂经理，可执行删除类业务操作"""
    roles = set(user_role_ids(user))
    return bool(roles & {SUPER_ADMIN_ROLE_ID, MANAGER_ROLE_ID})


class IsSuperAdmin(BasePermission):
    message = '仅超级管理员可执行该操作'

    def has_permission(self, request, view):
        return is_super_admin(request.user)


class BusinessPermission(BasePermission):
    """
    业务数据权限（客户 / 银行卡 / 交易）：
      - 读：任意已登录用户
      - 新增、修改：必须已分配角色（柜员及以上）
      - 删除：仅超级管理员或大堂经理
    """

    message = '当前账号未分配角色，无法执行业务操作'

    def has_permission(self, request, view):
        if not getattr(request.user, 'is_authenticated', False):
            return False
        if request.method in SAFE_METHODS:
            return True
        if not has_any_role(request.user):
            self.message = '当前账号未分配角色，无法执行业务操作'
            return False
        if request.method == 'DELETE' and not is_manager_or_admin(request.user):
            self.message = '仅超级管理员或大堂经理可删除业务数据'
            return False
        return True
