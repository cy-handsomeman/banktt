from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.card_info.models import CardInfo
from apps.sys_user.authentication import SysUserPrincipal
from apps.sys_user.models import SysUser
from apps.sys_user_role.models import SysUserRole
from apps.user_info.models import UserInfo


class CustomerDeleteTests(APITestCase):
    """客户删除保护与统一错误格式回归测试"""

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
        self.manager = SysUser.objects.create(
            user_name='test_manager', pid='110101199001010066', email='',
            mobile='13900000000', password=make_password('Test@12345'),
        )
        SysUserRole.objects.create(user_id=self.manager.user_id, role_id=2)
        self.client = APIClient()
        self.client.force_authenticate(user=SysUserPrincipal(self.manager))

    def test_customer_with_cards_cannot_be_deleted(self):
        response = self.client.delete(f'/api/user/{self.customer.customer_id}/')
        self.assertEqual(response.status_code, 400)
        self.assertIsInstance(response.data.get('detail'), str)
        self.assertTrue(UserInfo.objects.filter(pk=self.customer.pk).exists())
