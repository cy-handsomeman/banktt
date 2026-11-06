from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from rest_framework.test import APIClient, APITestCase

from apps.sys_user.authentication import SysUserPrincipal
from apps.sys_user.models import SysLoginLog, SysUser
from apps.sys_user_role.models import SysUserRole
from apps.user_info.models import UserInfo

ADMIN_ONLY_PATHS = (
    '/api/sys_user/',
    '/api/role/',
    '/api/menu/',
    '/api/role_menu/',
    '/api/sys_user_role/',
    '/api/login_log/',
)


class PermissionMatrixTests(APITestCase):
    """角色权限矩阵与路由暴露面回归测试"""

    def setUp(self):
        cache.clear()
        self.admin = self._make_user('test_admin', 1)
        self.manager = self._make_user('test_manager', 2)
        self.teller = self._make_user('test_teller', 3)

        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=SysUserPrincipal(self.admin))
        self.manager_client = APIClient()
        self.manager_client.force_authenticate(user=SysUserPrincipal(self.manager))
        self.teller_client = APIClient()
        self.teller_client.force_authenticate(user=SysUserPrincipal(self.teller))
        self.anon_client = APIClient()

    @staticmethod
    def _make_user(user_name, role_id):
        user = SysUser.objects.create(
            user_name=user_name, pid=f'11010119900101{role_id:04d}', email=f'{user_name}@example.com',
            mobile='13900000000', password=make_password('Test@12345'),
        )
        SysUserRole.objects.create(user_id=user.user_id, role_id=role_id)
        return user

    @staticmethod
    def _rows(response):
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data

    def test_admin_only_endpoints(self):
        for path in ADMIN_ONLY_PATHS:
            with self.subTest(path=path):
                self.assertEqual(self.anon_client.get(path).status_code, 401)
                self.assertEqual(self.admin_client.get(path).status_code, 200)
                self.assertEqual(self.manager_client.get(path).status_code, 403)
                self.assertEqual(self.teller_client.get(path).status_code, 403)

    def test_duplicate_fields_have_readable_messages(self):
        """重复用户名 / 身份证号应返回自定义中文提示，而不是模型名兜底文案"""
        payload = {
            'user_name': 'new_user_a',
            'password': 'Test@12345',
            'pid': self.admin.pid,
            'mobile': '13900009998',
        }
        response = self.admin_client.post('/api/sys_user/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data['pid'][0]), '该身份证号已存在，请勿重复录入')

        payload['user_name'] = self.admin.user_name
        payload['pid'] = '110101199001010098'
        response = self.admin_client.post('/api/sys_user/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data['user_name'][0]), '该用户名已存在，请更换')

    def test_business_read_allows_any_authenticated_role(self):
        for client in (self.admin_client, self.manager_client, self.teller_client):
            self.assertEqual(client.get('/api/user/').status_code, 200)
            self.assertEqual(client.get('/api/card/').status_code, 200)
            self.assertEqual(client.get('/api/trade/').status_code, 200)

    def test_write_role_can_create_and_readonly_role_cannot(self):
        payload = {
            'customer_name': '李四',
            'pid': '110101199001010099',
            'telephone': '13700000000',
            'address': '测试地址',
        }
        created = self.manager_client.post('/api/user/', payload, format='json')
        self.assertEqual(created.status_code, 201)
        customer_id = created.data['customer_id']

        denied = self.teller_client.post('/api/user/', payload, format='json')
        self.assertEqual(denied.status_code, 403)

        # 客户删除入口已移除：只读角色先被权限拦截，写角色命中不存在的 DELETE 方法
        self.assertEqual(self.teller_client.delete(f'/api/user/{customer_id}/').status_code, 403)
        self.assertEqual(self.manager_client.delete(f'/api/user/{customer_id}/').status_code, 405)
        self.assertTrue(UserInfo.objects.filter(customer_id=customer_id).exists())

    def test_page_prefix_no_longer_exposes_api_routes(self):
        self.assertEqual(self.admin_client.get('/user/user/').status_code, 404)
        self.assertEqual(self.admin_client.get('/sys_user/sys_user_list/').status_code, 404)
        self.assertEqual(self.admin_client.get('/card/card/').status_code, 404)

    def test_login_success_and_failure(self):
        client = APIClient()
        failed = client.post(
            '/api/sys_user/login/',
            {'userName': 'test_admin', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(failed.status_code, 401)

        success = client.post(
            '/api/sys_user/login/',
            {'userName': 'test_admin', 'password': 'Test@12345'},
            format='json',
        )
        self.assertEqual(success.status_code, 200)
        self.assertIn('access', success.data['data'])
        self.assertIn('refresh', success.data['data'])
        self.assertNotIn('password', success.data['data'])

    def test_password_hash_never_exposed(self):
        response = self.admin_client.get('/api/sys_user/')
        self.assertEqual(response.status_code, 200)
        for row in self._rows(response):
            self.assertNotIn('password', row)

    def test_login_sets_httponly_page_token_and_logout_clears_cookie(self):
        client = APIClient()
        response = client.post(
            '/api/sys_user/login/',
            {'userName': 'test_admin', 'password': 'Test@12345'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        cookie = response.cookies.get('page_token')
        self.assertIsNotNone(cookie)
        self.assertTrue(cookie.get('httponly'))
        self.assertEqual(cookie.get('samesite'), 'Lax')
        self.assertEqual(client.get('/').status_code, 200)
        for page in (
            '/dashboard/', '/user/', '/card/', '/trade/', '/transactions/',
            '/sys_user/', '/role/', '/login_log/',
        ):
            self.assertEqual(client.get(page).status_code, 200, page)

        logout = client.post('/api/sys_user/logout/')
        self.assertEqual(logout.status_code, 200)
        self.assertEqual(logout.cookies['page_token'].get('max-age'), 0)
        self.assertEqual(client.get('/').status_code, 302)

    def test_dashboard_summary_available_to_all_roles(self):
        for client in (self.admin_client, self.manager_client, self.teller_client):
            response = client.get('/api/dashboard/summary/')
            self.assertEqual(response.status_code, 200)
            for key in (
                'today_trade_count', 'today_trade_amount', 'customer_count',
                'card_count', 'card_normal_count', 'card_closed_count',
                'trend', 'latest_trades',
            ):
                self.assertIn(key, response.data)

    def test_menu_grants_match_role_matrix(self):
        def menu_count(client):
            response = client.get('/api/get_user_menu/')
            self.assertEqual(response.status_code, 200)
            return sum(len(group.get('items', [])) for group in response.data.get('menu', []))

        self.assertEqual(menu_count(self.admin_client), 8)
        self.assertEqual(menu_count(self.manager_client), 5)
        self.assertEqual(menu_count(self.teller_client), 4)

    def test_removed_pages_are_not_routed(self):
        self.assertEqual(self.admin_client.get('/menu/').status_code, 404)
        self.assertEqual(self.admin_client.get('/user_role/').status_code, 404)

