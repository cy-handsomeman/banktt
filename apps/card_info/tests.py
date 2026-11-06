from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.card_info.models import CardInfo
from apps.card_info.serializers import generate_card_id
from apps.sys_user.authentication import SysUserPrincipal
from apps.sys_user.models import SysUser
from apps.sys_user_role.models import SysUserRole
from apps.trade_info.models import TradeInfo
from apps.user_info.models import UserInfo

CARD_ID = '6222020000000011'


class CardStatusTests(APITestCase):
    """卡状态机与删除保护回归测试"""

    def setUp(self):
        cache.clear()
        self.customer = UserInfo.objects.create(
            customer_name='王五', pid='110101199001010033', telephone='13600000000'
        )
        self.card = CardInfo.objects.create(
            card_id=CARD_ID, cur_type='CNY', open_date=timezone.now(),
            open_money=Decimal('100.00'), balance=Decimal('100.00'), card_status='正常',
            password=make_password('123456'), customer_id=self.customer.customer_id,
        )
        self.manager = self._make_user('test_manager', 2)
        self.teller = self._make_user('test_teller', 3)
        self.manager_client = APIClient()
        self.manager_client.force_authenticate(user=SysUserPrincipal(self.manager))
        self.teller_client = APIClient()
        self.teller_client.force_authenticate(user=SysUserPrincipal(self.teller))

    @staticmethod
    def _make_user(user_name, role_id):
        user = SysUser.objects.create(
            user_name=user_name, pid='110101199001010044', email='',
            mobile='13900000000', password=make_password('Test@12345'),
        )
        SysUserRole.objects.create(user_id=user.user_id, role_id=role_id)
        return user

    def _refresh_card(self):
        self.card.refresh_from_db()

    def test_report_loss_and_unlock(self):
        response = self.manager_client.post(f'/api/card/{CARD_ID}/report-loss/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self._refresh_card()
        self.assertEqual(self.card.card_status, '挂失')

        repeat = self.manager_client.post(f'/api/card/{CARD_ID}/report-loss/', {}, format='json')
        self.assertEqual(repeat.status_code, 400)

        unlocked = self.manager_client.post(f'/api/card/{CARD_ID}/unlock/', {}, format='json')
        self.assertEqual(unlocked.status_code, 200)
        self._refresh_card()
        self.assertEqual(self.card.card_status, '正常')

    def test_close_rejected_when_balance_not_zero(self):
        response = self.manager_client.post(f'/api/card/{CARD_ID}/close/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        self._refresh_card()
        self.assertEqual(self.card.card_status, '正常')

    def test_teller_cannot_close_card(self):
        self.card.balance = Decimal('0.00')
        self.card.save(update_fields=['balance'])
        response = self.teller_client.post(f'/api/card/{CARD_ID}/close/', {}, format='json')
        self.assertEqual(response.status_code, 403)
        self._refresh_card()
        self.assertEqual(self.card.card_status, '正常')

        manager_response = self.manager_client.post(f'/api/card/{CARD_ID}/close/', {}, format='json')
        self.assertEqual(manager_response.status_code, 200)
        self._refresh_card()
        self.assertEqual(self.card.card_status, '销户')

    def test_query_officer_cannot_write_card(self):
        response = self.teller_client.post(f'/api/card/{CARD_ID}/report-loss/', {}, format='json')
        self.assertEqual(response.status_code, 403)
        self._refresh_card()
        self.assertEqual(self.card.card_status, '正常')

    def test_card_cannot_be_deleted(self):
        TradeInfo.objects.create(
            trans_type='存款', card_id=CARD_ID, trans_date=timezone.now(),
            trans_money=Decimal('10.00'), balance_after=Decimal('110.00'),
        )
        response = self.manager_client.delete(f'/api/card/{CARD_ID}/')
        self.assertEqual(response.status_code, 405)
        self.assertTrue(CardInfo.objects.filter(card_id=CARD_ID).exists())

    def _create_card_payload(self, customer_id, card_id=None):
        payload = {
            'cur_type': 'CNY',
            'open_date': timezone.now().isoformat(),
            'open_money': '50.00',
            'customer_id': customer_id,
            'password': '123456',
        }
        if card_id:
            payload['card_id'] = card_id
        return payload

    def test_card_id_generated_by_server_and_client_value_ignored(self):
        response = self.manager_client.post(
            '/api/card/', self._create_card_payload(self.customer.customer_id, '9999999999999999'),
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertRegex(response.data['card_id'], r'^622202\d{10}$')
        self.assertNotEqual(response.data['card_id'], '9999999999999999')
        self.assertEqual(response.data['balance'], '50.00')

    def test_same_customer_can_hold_multiple_cards(self):
        first = self.manager_client.post(
            '/api/card/', self._create_card_payload(self.customer.customer_id), format='json'
        )
        second = self.manager_client.post(
            '/api/card/', self._create_card_payload(self.customer.customer_id), format='json'
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertNotEqual(first.data['card_id'], second.data['card_id'])

    def test_create_card_requires_existing_customer(self):
        response = self.manager_client.post(
            '/api/card/', self._create_card_payload(999999), format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('customer_id', response.data)

    def test_card_customer_cannot_be_changed(self):
        other = UserInfo.objects.create(
            customer_name='赵六', pid='110101199001010055', telephone='13700000000'
        )
        payload = self._create_card_payload(other.customer_id)
        payload.pop('password')
        response = self.manager_client.put(f'/api/card/{CARD_ID}/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('customer_id', response.data)
        self._refresh_card()
        self.assertEqual(self.card.customer_id, self.customer.customer_id)

    def test_generate_card_id_format_and_uniqueness(self):
        """卡号生成器应产出 622202 开头的 16 位数字，且样本内不重复"""
        generated = [generate_card_id() for _ in range(50)]
        for card_id in generated:
            self.assertRegex(card_id, r'^622202\d{10}$')
        self.assertEqual(len(set(generated)), len(generated))

    @patch('apps.card_info.serializers.generate_card_id')
    def test_create_card_retries_when_generated_id_exists(self, mocked_generate):
        """生成的卡号与已有卡号冲突时应自动换号重试"""
        mocked_generate.side_effect = [CARD_ID, '6222029999999999']
        response = self.manager_client.post(
            '/api/card/', self._create_card_payload(self.customer.customer_id), format='json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['card_id'], '6222029999999999')

    @patch('apps.card_info.serializers.generate_card_id', return_value=CARD_ID)
    def test_create_card_fails_after_repeated_card_id_collisions(self, mocked_generate):
        """连续多次生成的卡号都冲突时返回明确错误，不落库"""
        response = self.manager_client.post(
            '/api/card/', self._create_card_payload(self.customer.customer_id), format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('card_id', response.data)
        self.assertEqual(CardInfo.objects.filter(card_id=CARD_ID).count(), 1)

    def test_customer_options_lists_registered_customers(self):
        """客户下拉只返回已注册客户，按编号升序，且字段精简"""
        second = UserInfo.objects.create(
            customer_name='赵六', pid='110101199001010055', telephone='13700000000'
        )
        response = self.manager_client.get('/api/user/options/')
        self.assertEqual(response.status_code, 200)
        ids = [item['customer_id'] for item in response.data]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(set(ids), {self.customer.customer_id, second.customer_id})
        self.assertEqual(set(response.data[0].keys()), {'customer_id', 'customer_name'})

    def test_query_officer_can_read_customer_options(self):
        """查询员只读，但可以读取客户下拉数据"""
        response = self.teller_client.get('/api/user/options/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(item['customer_id'] == self.customer.customer_id for item in response.data))

    def test_customer_options_requires_login(self):
        """未登录不能读取客户下拉数据"""
        response = APIClient().get('/api/user/options/')
        self.assertEqual(response.status_code, 401)

    def test_customer_options_empty_without_customers(self):
        """没有任何注册客户时下拉返回空列表，前端据此提示先新增客户"""
        CardInfo.objects.all().delete()  # 卡依赖客户，需先清理卡再清客户
        UserInfo.objects.all().delete()
        response = self.manager_client.get('/api/user/options/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
