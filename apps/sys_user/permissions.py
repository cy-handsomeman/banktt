from django.conf import settings
from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.sys_user_role.models import SysUserRole

# 角色 ID 从配置读取，避免在代码里散落魔法数字
SUPER_ADMIN_ROLE_ID = getattr(settings, 'SUPER_ADMIN_ROLE_ID', 1)  # 管理员
MANAGER_ROLE_ID = getattr(settings, 'MANAGER_ROLE_ID', 2)  # 柜员
TELLER_ROLE_ID = getattr(settings, 'TELLER_ROLE_ID', 3)  # 查询员

# 具备业务写权限的角色：管理员与柜员
WRITE_ROLE_IDS = frozenset({SUPER_ADMIN_ROLE_ID, MANAGER_ROLE_ID})


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
    """判断当前登录用户是否绑定了管理员角色"""
    return SUPER_ADMIN_ROLE_ID in user_role_ids(user)


def is_write_role(user):
    """管理员或柜员可执行业务写操作；查询员只读"""
    roles = set(user_role_ids(user))
    return bool(roles & WRITE_ROLE_IDS)


class IsSuperAdmin(BasePermission):
    message = '仅管理员可执行该操作'

    def has_permission(self, request, view):
        return is_super_admin(request.user)


class BusinessPermission(BasePermission):
    """
    业务数据权限（客户 / 银行卡 / 交易）：
      - 读：任意已登录用户（含查询员）
      - 写：仅管理员与柜员
    """

    message = '当前角色为只读，不能执行该操作'

    def has_permission(self, request, view):
        if not getattr(request.user, 'is_authenticated', False):
            return False
        if request.method in SAFE_METHODS:
            return True
        if not is_write_role(request.user):
            self.message = '当前角色为只读，不能执行该操作'
            return False
        return True
