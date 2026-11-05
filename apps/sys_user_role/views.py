from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from drf_spectacular.utils import extend_schema, OpenApiTypes
from apps.sys_user_role.models import SysUserRole
from apps.sys_user_role.serializers import SysUserRoleSerializer
from apps.sys_role_menu.models import SysRoleMenu
from apps.sys_menu.models import SysMenu
from apps.sys_role.models import SysRole
from apps.sys_user.permissions import (
    IsSuperAdmin,
    SUPER_ADMIN_ROLE_ID,
    user_role_ids,
)


# 菜单分组 / 图标全部来自 sys_menu 表，代码里不再维护任何 URL 映射
DEFAULT_GROUP = '其他'
DEFAULT_ICON = 'fas fa-circle'


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _super_admin_user_ids():
    return set(
        SysUserRole.objects.filter(role_id=SUPER_ADMIN_ROLE_ID)
        .values_list('user_id', flat=True)
    )


def _guard_super_admin_removal(request, user_ids, removing_super_admin):
    """保护超管绑定：不能移除自己的，也不能让系统失去最后一名超管"""
    if not removing_super_admin:
        return
    targets = set()
    for user_id in user_ids:
        parsed = _to_int(user_id)
        if parsed is None:
            raise ValidationError({'detail': '用户ID格式不正确'})
        targets.add(parsed)
    if request.user.pk in targets:
        raise ValidationError({'detail': '不能移除自己的超级管理员角色'})
    remaining = _super_admin_user_ids() - targets
    if not remaining:
        raise ValidationError({'detail': '系统必须保留至少一名超级管理员'})


def _normalize_url(url):
    url = (url or '').strip()
    if not url:
        return '/'
    if not url.startswith('/'):
        url = '/' + url
    if not url.endswith('/'):
        url += '/'
    return url


def _menu_key(url):
    return _normalize_url(url).strip('/').replace('/', '_')


def _build_menu(menus):
    """按 sys_menu 表的字段构建前端导航（分组、图标、排序均以数据库为准）"""
    groups = {}
    for menu in menus:
        url = _normalize_url(menu.menu_url)
        group_name = (menu.menu_group or '').strip() or DEFAULT_GROUP
        groups.setdefault(group_name, []).append({
            'key': _menu_key(url),
            'title': menu.menu_name,
            'icon': (menu.icon or '').strip() or DEFAULT_ICON,
            'url': url,
            'order': menu.sort_order or 0,
            'menu_id': menu.menu_id,
        })

    for items in groups.values():
        items.sort(key=lambda item: (item['order'], item['menu_id']))

    # 分组顺序按组内最小排序号排列，全部由数据库决定
    ordered_group_names = sorted(
        groups, key=lambda name: min(item['order'] for item in groups[name])
    )
    user_menu = []
    for group_name in ordered_group_names:
        user_menu.append({
            'group': group_name,
            'items': groups[group_name],
            'locked': False,
        })
    return user_menu


@extend_schema(responses={200: OpenApiTypes.OBJECT})
@api_view(['GET'])
def check_super_admin(request):
    """
    检查当前登录用户是否是超级管理员
    GET /api/check_super_admin/
    """
    return Response(
        {'is_super_admin': SUPER_ADMIN_ROLE_ID in user_role_ids(request.user)},
        status=status.HTTP_200_OK
    )


@extend_schema(responses={200: OpenApiTypes.OBJECT})
@api_view(['GET'])
def get_user_menu(request):
    """
    获取当前登录用户有权限访问的菜单列表（完全由 sys_menu + sys_role_menu 驱动）
    GET /api/get_user_menu/
    """
    user_id = request.user.pk
    user_roles = sorted(user_role_ids(request.user))
    is_super_admin = SUPER_ADMIN_ROLE_ID in user_roles

    if is_super_admin:
        menus = SysMenu.objects.all()
    else:
        menu_ids = set(
            SysRoleMenu.objects.filter(role_id__in=user_roles).values_list('menu_id', flat=True)
        )
        menus = SysMenu.objects.filter(menu_id__in=menu_ids)

    menus = list(menus.order_by('sort_order', 'menu_id'))
    user_menu = _build_menu(menus)

    # 角色名称直接从 sys_role 表读取，避免代码里维护一份容易过期的映射
    role_name_map = dict(
        SysRole.objects.filter(role_id__in=user_roles).values_list('role_id', 'role_name')
    )
    role_names = [role_name_map.get(role_id, f'未知角色({role_id})') for role_id in user_roles]
    role_names_str = ', '.join(role_names) if role_names else '无角色'

    return Response({
        'user_id': user_id,
        'user_roles': user_roles,
        'role_names': role_names,
        'role_names_str': role_names_str,
        'is_super_admin': is_super_admin,
        'menu': user_menu,
    })


class SysUserRoleViewSet(viewsets.ModelViewSet):
    queryset = SysUserRole.objects.all().order_by('user_id', 'role_id')
    serializer_class = SysUserRoleSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['user_id', 'role_id']

    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def get_user_roles(self, request, user_id=None):
        """
        获取用户拥有的角色列表
        GET /api/user_role/user/{user_id}/
        """
        parsed_user_id = _to_int(user_id)
        if parsed_user_id is None:
            raise ValidationError({'detail': '用户ID格式不正确'})
        user_roles = SysUserRole.objects.filter(user_id=parsed_user_id)
        serializer = self.get_serializer(user_roles, many=True)
        return Response({'user_id': parsed_user_id, 'roles': serializer.data})

    @action(detail=False, methods=['get'], url_path='role/(?P<role_id>[^/.]+)')
    def get_role_users(self, request, role_id=None):
        """
        查询角色关联的用户列表
        GET /api/user_role/role/{role_id}/
        """
        parsed_role_id = _to_int(role_id)
        if parsed_role_id is None:
            raise ValidationError({'detail': '角色ID格式不正确'})
        role_users = SysUserRole.objects.filter(role_id=parsed_role_id)
        serializer = self.get_serializer(role_users, many=True)
        return Response({'role_id': parsed_role_id, 'users': serializer.data})

    @action(detail=False, methods=['get'], url_path='check')
    def check_user_role(self, request):
        """
        判断用户是否拥有特定角色
        GET /api/user_role/check?user_id={user_id}&role_id={role_id}
        """
        user_id = _to_int(request.query_params.get('user_id'))
        role_id = _to_int(request.query_params.get('role_id'))
        if user_id is None or role_id is None:
            raise ValidationError({'detail': '缺少参数 user_id 或 role_id，且必须为整数'})

        exists = SysUserRole.objects.filter(user_id=user_id, role_id=role_id).exists()
        return Response({
            'user_id': user_id,
            'role_id': role_id,
            'has_role': exists
        })

    @action(detail=False, methods=['post'], url_path='batch_remove')
    def batch_remove_roles(self, request):
        """
        批量移除角色
        POST /api/user_role/batch_remove/
        {
            "user_ids": [1, 2, 3],
            "role_id": 1
        }
        """
        user_ids = request.data.get('user_ids') or []
        role_id = _to_int(request.data.get('role_id'))
        if not user_ids or role_id is None:
            raise ValidationError(
                {'detail': '缺少参数 user_ids 或 role_id，且 role_id 必须为整数'}
            )

        parsed_user_ids = [_to_int(user_id) for user_id in user_ids]
        if any(user_id is None for user_id in parsed_user_ids):
            raise ValidationError({'detail': '用户ID格式不正确'})

        _guard_super_admin_removal(
            request, parsed_user_ids, role_id == SUPER_ADMIN_ROLE_ID
        )

        with transaction.atomic():
            deleted_count, _ = SysUserRole.objects.filter(
                user_id__in=parsed_user_ids,
                role_id=role_id
            ).delete()

        return Response({
            'deleted': deleted_count,
            'message': f'成功移除 {deleted_count} 个角色关联'
        })

    @action(detail=False, methods=['post'], url_path='user/(?P<user_id>[^/.]+)/clear')
    def remove_user_all_roles(self, request, user_id=None):
        """
        清空用户的所有角色
        POST /api/user_role/user/{user_id}/clear/
        """
        parsed_user_id = _to_int(user_id)
        if parsed_user_id is None:
            raise ValidationError({'detail': '用户ID格式不正确'})

        # 清空角色必然包含超管角色，同样需要防止把自己或最后一名超管移除
        _guard_super_admin_removal(request, [parsed_user_id], True)

        with transaction.atomic():
            deleted_count, _ = SysUserRole.objects.filter(user_id=parsed_user_id).delete()
        return Response({
            'deleted': deleted_count,
            'message': f'成功移除用户 {parsed_user_id} 的 {deleted_count} 个角色'
        })

    def perform_destroy(self, instance):
        """单独删除某个角色绑定时，也要保护超管绑定"""
        _guard_super_admin_removal(
            self.request,
            [instance.user_id],
            instance.role_id == SUPER_ADMIN_ROLE_ID
        )
        with transaction.atomic():
            instance.delete()

    def create(self, request, *args, **kwargs):
        """
        单个角色分配（重写以处理重复关联）
        """
        user_id = _to_int(request.data.get('user_id'))
        role_id = _to_int(request.data.get('role_id'))
        if user_id is None or role_id is None:
            return Response(
                {'detail': 'user_id 与 role_id 必须为整数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 先检查是否已存在
        if SysUserRole.objects.filter(user_id=user_id, role_id=role_id).exists():
            return Response(
                {'detail': '该用户已拥有此角色'},
                status=status.HTTP_409_CONFLICT
            )

        return super().create(request, *args, **kwargs)
