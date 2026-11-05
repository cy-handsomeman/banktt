from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.card_info.models import CardInfo
from apps.sys_user.authentication import SysUserPrincipal
from apps.sys_user.models import SysUser
from apps.sys_user_role.models import SysUserRole
from apps.user_info.models import UserInfo


class CustomerPermissionTests(APITestCase):
    """客户资料权限回归：查询员只读，写操作仅管理员/柜员，且不提供删除"""

    def setUp(self):
        cache.clear()
        self.customer = UserInfo.objects.create(
            customer_name='赵六', pid='110101199001010055', telephone='13500000000'
        )
        CardInfo.objects.create(
            card_id='6222020000000022', cur_type='CNY', open_date=timezone.now(),
            open_money=0, balance=0, card_status='正常',
            password=make_password('123456'), customer_id=self.customer.customer_id,
        )
        self.manager = self._make_user('test_manager', 2)
        self.query_officer = self._make_user('test_teller', 3)
        self.manager_client = APIClient()
        self.manager_client.force_authenticate(user=SysUserPrincipal(self.manager))
        self.read_client = APIClient()
        self.read_client.force_authenticate(user=SysUserPrincipal(self.query_officer))

    @staticmethod
    def _make_user(user_name, role_id):
        user = SysUser.objects.create(
            user_name=user_name, pid='110101199001010066', email='',
            mobile='13900000000', password=make_password('Test@12345'),
        )
        SysUserRole.objects.create(user_id=user.user_id, role_id=role_id)
        return user

    def test_customer_cannot_be_deleted(self):
        response = self.manager_client.delete(f'/api/user/{self.customer.customer_id}/')
        self.assertEqual(response.status_code, 405)
        self.assertTrue(UserInfo.objects.filter(pk=self.customer.pk).exists())

    def test_query_officer_cannot_write_customer(self):
        created = self.read_client.post(
            '/api/user/',
            {'customer_name': '钱七', 'pid': '110101199001010077', 'telephone': '13800001111'},
            format='json',
        )
        self.assertEqual(created.status_code, 403)

        updated = self.read_client.put(
            f'/api/user/{self.customer.customer_id}/',
            {'customer_name': '赵六改', 'pid': self.customer.pid, 'telephone': self.customer.telephone},
            format='json',
        )
        self.assertEqual(updated.status_code, 403)

    def test_manager_can_create_and_update_customer(self):
        created = self.manager_client.post(
            '/api/user/',
            {'customer_name': '钱七', 'pid': '110101199001010077', 'telephone': '13800001111'},
            format='json',
        )
        self.assertEqual(created.status_code, 201)

        updated = self.manager_client.put(
            f'/api/user/{self.customer.customer_id}/',
            {'customer_name': '赵六改', 'pid': self.customer.pid, 'telephone': self.customer.telephone},
            format='json',
        )
        self.assertEqual(updated.status_code, 200)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.customer_name, '赵六改')

    def test_query_officer_can_read_customer(self):
        listed = self.read_client.get('/api/user/')
        self.assertEqual(listed.status_code, 200)
        detail = self.read_client.get(f'/api/user/{self.customer.customer_id}/')
        self.assertEqual(detail.status_code, 200)
