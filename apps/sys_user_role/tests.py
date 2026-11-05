from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from rest_framework.test import APIClient, APITestCase

from apps.sys_menu.models import SysMenu
from apps.sys_role_menu.models import SysRoleMenu
from apps.sys_user.authentication import SysUserPrincipal
from apps.sys_user.models import SysUser
from apps.sys_user_role.models import SysUserRole


class AdminGuardTests(APITestCase):
    """管理端保护规则：超管绑定、重复授权、菜单删除"""

    def setUp(self):
        cache.clear()
        self.admin = SysUser.objects.create(
            user_name='test_admin',
            pid='110101199001010001',
            email='',
            mobile='13900000000',
            password=make_password('Test@12345'),
        )
        SysUserRole.objects.create(user_id=self.admin.user_id, role_id=1)
        self.client = APIClient()
        self.client.force_authenticate(user=SysUserPrincipal(self.admin))

    def test_cannot_remove_own_super_admin_binding(self):
        binding = SysUserRole.objects.get(user_id=self.admin.user_id, role_id=1)
        response = self.client.delete(f'/api/sys_user_role/{binding.pk}/')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(SysUserRole.objects.filter(pk=binding.pk).exists())

        cleared = self.client.post(f'/api/sys_user_role/user/{self.admin.user_id}/clear/')
        self.assertEqual(cleared.status_code, 400)

    def test_duplicate_role_menu_binding_returns_409(self):
        menu = SysMenu.objects.create(
            menu_name='临时菜单', menu_url='/tmp_menu/', menu_group='临时', sort_order=99
        )
        first = self.client.post(
            '/api/role_menu/', {'role_id': 2, 'menu_id': menu.menu_id}, format='json'
        )
        self.assertEqual(first.status_code, 201)

        second = self.client.post(
            '/api/role_menu/', {'role_id': 2, 'menu_id': menu.menu_id}, format='json'
        )
        self.assertEqual(second.status_code, 409)
        self.assertIsInstance(second.data.get('detail'), str)

    def test_menu_delete_protection(self):
        parent = SysMenu.objects.create(
            menu_name='临时父菜单', menu_url='/tmp_parent/', menu_group='临时', sort_order=99
        )
        child = SysMenu.objects.create(
            menu_name='临时子菜单', menu_url='/tmp_child/', menu_group='临时',
            sort_order=99, parent_id=parent.menu_id,
        )

        parent_response = self.client.delete(f'/api/menu/{parent.menu_id}/')
        self.assertEqual(parent_response.status_code, 400)
        self.assertIsInstance(parent_response.data.get('detail'), str)

        SysRoleMenu.objects.create(role_id=2, menu_id=child.menu_id)
        granted_response = self.client.delete(f'/api/menu/{child.menu_id}/')
        self.assertEqual(granted_response.status_code, 400)
        self.assertIsInstance(granted_response.data.get('detail'), str)

        SysRoleMenu.objects.filter(role_id=2, menu_id=child.menu_id).delete()
        self.assertEqual(self.client.delete(f'/api/menu/{child.menu_id}/').status_code, 204)
        self.assertEqual(self.client.delete(f'/api/menu/{parent.menu_id}/').status_code, 204)
