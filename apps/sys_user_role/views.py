from django.shortcuts import render
from django.db import IntegrityError
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
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


def sys_user_role_list(request):
    return render(request, 'sys_user_role.html')


# 菜单展示配置：只负责图标和分组归属，菜单本身（名称/地址/排序）以 sys_menu 表为准
MENU_PRESENTATION = {
    '/user/': {'icon': 'fas fa-users', 'group': '业务管理'},
    '/card/': {'icon': 'fas fa-credit-card', 'group': '业务管理'},
    '/trade/': {'icon': 'fas fa-exchange-alt', 'group': '业务管理'},
    '/sys_user/': {'icon': 'fas fa-user-circle', 'group': '权限管理'},
    '/role/': {'icon': 'fas fa-shield-alt', 'group': '权限管理'},
    '/user_role/': {'icon': 'fas fa-user-shield', 'group': '权限管理'},
}
GROUP_ORDER = ['业务管理', '权限管理']
DEFAULT_GROUP = '其他'
DEFAULT_ICON = 'fas fa-circle'


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
    """按 sys_menu 表构建前端导航，分组与图标来自 MENU_PRESENTATION"""
    groups = {}
    for menu in menus:
        url = _normalize_url(menu.menu_url)
        presentation = MENU_PRESENTATION.get(url, {})
        group_name = presentation.get('group', DEFAULT_GROUP)
        groups.setdefault(group_name, []).append({
            'key': _menu_key(url),
            'title': menu.menu_name,
            'icon': presentation.get('icon', DEFAULT_ICON),
            'url': url,
            'order': menu.sort_order or 0,
            'menu_id': menu.menu_id,
        })

    for items in groups.values():
        items.sort(key=lambda item: (item['order'], item['menu_id']))

    ordered_group_names = GROUP_ORDER + sorted(
        name for name in groups if name not in GROUP_ORDER
    )
    user_menu = []
    for group_name in ordered_group_names:
        if groups.get(group_name):
            user_menu.append({
                'group': group_name,
                'items': groups[group_name],
                'locked': False,
            })
    return user_menu


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
        try:
            user_roles = SysUserRole.objects.filter(user_id=user_id)
            serializer = self.get_serializer(user_roles, many=True)
            return Response({'user_id': user_id, 'roles': serializer.data})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='role/(?P<role_id>[^/.]+)')
    def get_role_users(self, request, role_id=None):
        """
        查询角色关联的用户列表
        GET /api/user_role/role/{role_id}/
        """
        try:
            role_users = SysUserRole.objects.filter(role_id=role_id)
            serializer = self.get_serializer(role_users, many=True)
            return Response({'role_id': role_id, 'users': serializer.data})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='check')
    def check_user_role(self, request):
        """
        判断用户是否拥有特定角色
        GET /api/user_role/check?user_id={user_id}&role_id={role_id}
        """
        try:
            user_id = request.query_params.get('user_id')
            role_id = request.query_params.get('role_id')
            
            if not user_id or not role_id:
                return Response(
                    {'error': '缺少参数 user_id 或 role_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            exists = SysUserRole.objects.filter(user_id=user_id, role_id=role_id).exists()
            return Response({
                'user_id': user_id,
                'role_id': role_id,
                'has_role': exists
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

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
        try:
            user_ids = request.data.get('user_ids', [])
            role_id = request.data.get('role_id')
            
            if not user_ids or not role_id:
                return Response(
                    {'error': '缺少参数 user_ids 或 role_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            deleted_count, _ = SysUserRole.objects.filter(
                user_id__in=user_ids,
                role_id=role_id
            ).delete()
            
            return Response({
                'deleted': deleted_count,
                'message': f'成功移除 {deleted_count} 个角色关联'
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], url_path='user/(?P<user_id>[^/.]+)/clear')
    def remove_user_all_roles(self, request, user_id=None):
        """
        清空用户的所有角色
        POST /api/user_role/user/{user_id}/clear/
        """
        try:
            deleted_count, _ = SysUserRole.objects.filter(user_id=user_id).delete()
            return Response({
                'deleted': deleted_count,
                'message': f'成功移除用户 {user_id} 的 {deleted_count} 个角色'
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request, *args, **kwargs):
        """
        单个角色分配（重写以处理重复关联）
        """
        user_id = request.data.get('user_id')
        role_id = request.data.get('role_id')
        
        # 先检查是否已存在
        if SysUserRole.objects.filter(user_id=user_id, role_id=role_id).exists():
            return Response(
                {'error': '该用户已拥有此角色'},
                status=status.HTTP_409_CONFLICT
            )
        
        return super().create(request, *args, **kwargs)
