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

    def test_binding_with_missing_user_or_role_returns_400(self):
        missing_user = self.client.post(
            '/api/sys_user_role/', {'user_id': 999999, 'role_id': 1}, format='json'
        )
        self.assertEqual(missing_user.status_code, 400)
        self.assertIsInstance(missing_user.data.get('detail'), str)

        missing_role = self.client.post(
            '/api/sys_user_role/', {'user_id': self.admin.user_id, 'role_id': 999999}, format='json'
        )
        self.assertEqual(missing_role.status_code, 400)
        self.assertIsInstance(missing_role.data.get('detail'), str)

    def test_duplicate_user_role_binding_returns_409(self):
        response = self.client.post(
            '/api/sys_user_role/', {'user_id': self.admin.user_id, 'role_id': 1}, format='json'
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(SysUserRole.objects.filter(user_id=self.admin.user_id, role_id=1).count(), 1)

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


class SingleRolePolicyTests(APITestCase):
    """单选策略：一个用户最多一个角色，改角色统一走 set_role 原子接口"""

    def setUp(self):
        cache.clear()
        self.admin = SysUser.objects.create(
            user_name='policy_admin',
            pid='110101199001010071',
            email='',
            mobile='13900000001',
            password=make_password('Test@12345'),
        )
        SysUserRole.objects.create(user_id=self.admin.user_id, role_id=1)

        self.teller = SysUser.objects.create(
            user_name='policy_teller',
            pid='110101199001010072',
            email='',
            mobile='13900000002',
            password=make_password('Test@12345'),
        )
        SysUserRole.objects.create(user_id=self.teller.user_id, role_id=2)

        self.client = APIClient()
        self.client.force_authenticate(user=SysUserPrincipal(self.admin))

    def _bindings(self, user_id):
        return set(
            SysUserRole.objects.filter(user_id=user_id).values_list('role_id', flat=True)
        )

    def test_set_role_replaces_existing_role(self):
        response = self.client.post(
            f'/api/sys_user_role/user/{self.teller.user_id}/set_role/',
            {'role_id': 3}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._bindings(self.teller.user_id), {3})

    def test_set_role_null_clears_roles(self):
        response = self.client.post(
            f'/api/sys_user_role/user/{self.teller.user_id}/set_role/',
            {'role_id': None}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._bindings(self.teller.user_id), set())

    def test_set_role_rejects_self_demote(self):
        response = self.client.post(
            f'/api/sys_user_role/user/{self.admin.user_id}/set_role/',
            {'role_id': 2}, format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._bindings(self.admin.user_id), {1})

    def test_set_role_allows_changing_other_admin(self):
        other = SysUser.objects.create(
            user_name='policy_admin2',
            pid='110101199001010073',
            email='',
            mobile='13900000003',
            password=make_password('Test@12345'),
        )
        SysUserRole.objects.create(user_id=other.user_id, role_id=1)
        response = self.client.post(
            f'/api/sys_user_role/user/{other.user_id}/set_role/',
            {'role_id': 2}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._bindings(other.user_id), {2})

    def test_create_rejects_user_with_other_role(self):
        response = self.client.post(
            '/api/sys_user_role/',
            {'user_id': self.teller.user_id, 'role_id': 3},
            format='json',
        )
        self.assertEqual(response.status_code, 409)
        self.assertTrue(response.data.get('has_role'))
        self.assertEqual(response.data.get('current_role_id'), 2)
        self.assertEqual(self._bindings(self.teller.user_id), {2})

    def test_create_same_role_still_returns_409_without_has_role(self):
        response = self.client.post(
            '/api/sys_user_role/',
            {'user_id': self.teller.user_id, 'role_id': 2},
            format='json',
        )
        self.assertEqual(response.status_code, 409)
        self.assertIsInstance(response.data.get('detail'), str)
        self.assertFalse(response.data.get('has_role'))
        self.assertEqual(self._bindings(self.teller.user_id), {2})
