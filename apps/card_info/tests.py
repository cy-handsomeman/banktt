from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.hashers import check_password, make_password
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
            card_id=CARD_ID, cur_type='人民币', open_date=timezone.now(),
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
            user_name=user_name, pid=f'11010119900101{role_id:04d}', email='',
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
            'cur_type': '人民币',
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

    def test_list_and_retrieve_card(self):
        """列表分页结构与详情接口均返回卡号，且不暴露密码"""
        list_resp = self.manager_client.get('/api/card/')
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.data['count'], 1)
        self.assertEqual(list_resp.data['results'][0]['card_id'], CARD_ID)

        detail = self.manager_client.get(f'/api/card/{CARD_ID}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data['card_id'], CARD_ID)
        self.assertNotIn('password', detail.data)

    def test_card_list_exposes_customer_name(self):
        """卡列表和详情都要返回客户姓名，前端不再只显示数字客户ID"""
        list_resp = self.manager_client.get('/api/card/')
        self.assertEqual(list_resp.status_code, 200)
        row = list_resp.data['results'][0]
        self.assertEqual(row['customer_id'], self.customer.customer_id)
        self.assertEqual(row['customer_name'], '王五')

        detail = self.manager_client.get(f'/api/card/{CARD_ID}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data['customer_name'], '王五')

    def test_customer_cards_filter_used_by_customer_page(self):
        """客户管理页按 customer_id 过滤时，只返回该客户名下的卡"""
        other = UserInfo.objects.create(
            customer_name='赵六', pid='110101199001010055', telephone='13700000000'
        )
        CardInfo.objects.create(
            card_id='6222020000000022', cur_type='美元', open_date=timezone.now(),
            open_money=Decimal('20.00'), balance=Decimal('20.00'), card_status='正常',
            password=make_password('123456'), customer_id=other.customer_id,
        )
        response = self.manager_client.get('/api/card/', {
            'customer_id': self.customer.customer_id,
            'page_size': 100,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual([c['card_id'] for c in response.data['results']], [CARD_ID])
        self.assertEqual(response.data['results'][0]['customer_name'], '王五')

    def test_list_filters_and_search(self):
        """列表支持按货币类型、状态、客户与卡号搜索"""
        other = UserInfo.objects.create(
            customer_name='赵六', pid='110101199001010055', telephone='13700000000'
        )
        CardInfo.objects.create(
            card_id='6222020000000022', cur_type='美元', open_date=timezone.now(),
            open_money=Decimal('20.00'), balance=Decimal('20.00'), card_status='挂失',
            password=make_password('123456'), customer_id=other.customer_id,
        )

        by_type = self.manager_client.get('/api/card/', {'cur_type': '美元'})
        self.assertEqual(by_type.status_code, 200)
        self.assertEqual([c['card_id'] for c in by_type.data['results']], ['6222020000000022'])

        by_status = self.manager_client.get('/api/card/?card_status=挂失')
        self.assertEqual([c['card_id'] for c in by_status.data['results']], ['6222020000000022'])

        by_customer = self.manager_client.get(f'/api/card/?customer_id={self.customer.customer_id}')
        self.assertEqual([c['card_id'] for c in by_customer.data['results']], [CARD_ID])

        by_search = self.manager_client.get('/api/card/?search=0022')
        self.assertEqual([c['card_id'] for c in by_search.data['results']], ['6222020000000022'])

    def test_query_officer_can_list_and_retrieve_cards(self):
        """查询员只读，但可以查看卡列表与详情"""
        self.assertEqual(self.teller_client.get('/api/card/').status_code, 200)
        self.assertEqual(self.teller_client.get(f'/api/card/{CARD_ID}/').status_code, 200)

    def test_retrieve_and_update_nonexistent_card(self):
        self.assertEqual(self.manager_client.get('/api/card/999999/').status_code, 404)
        response = self.manager_client.put(
            '/api/card/999999/', self._create_card_payload(self.customer.customer_id), format='json'
        )
        self.assertEqual(response.status_code, 404)

    def test_create_requires_password(self):
        payload = self._create_card_payload(self.customer.customer_id)
        payload.pop('password')
        response = self.manager_client.post('/api/card/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.data)

    def test_create_password_is_hashed(self):
        response = self.manager_client.post(
            '/api/card/', self._create_card_payload(self.customer.customer_id), format='json'
        )
        self.assertEqual(response.status_code, 201)
        created = CardInfo.objects.get(card_id=response.data['card_id'])
        self.assertTrue(check_password('123456', created.password))
        self.assertNotEqual(created.password, '123456')

    def test_create_rejects_negative_open_money(self):
        payload = self._create_card_payload(self.customer.customer_id)
        payload['open_money'] = '-1.00'
        response = self.manager_client.post('/api/card/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('open_money', response.data)

    def test_create_rejects_invalid_currency(self):
        """货币类型只接受人民币/美元/欧元/港币，历史代码 RMB 不得再写入"""
        payload = self._create_card_payload(self.customer.customer_id)
        payload['cur_type'] = 'RMB'
        response = self.manager_client.post('/api/card/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('cur_type', response.data)
        self.assertEqual(CardInfo.objects.count(), 1)

    def test_update_rejects_invalid_currency(self):
        response = self.manager_client.put(
            f'/api/card/{CARD_ID}/', {
                'cur_type': 'CNY',
                'open_date': timezone.now().isoformat(),
            }, format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('cur_type', response.data)
        self._refresh_card()
        self.assertEqual(self.card.cur_type, '人民币')

    def test_create_ignores_client_balance_and_status(self):
        """客户端传入的余额与状态无效，初始余额恒等于开户金额"""
        payload = self._create_card_payload(self.customer.customer_id)
        payload['balance'] = '999.00'
        payload['card_status'] = '挂失'
        response = self.manager_client.post('/api/card/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['balance'], '50.00')
        created = CardInfo.objects.get(card_id=response.data['card_id'])
        self.assertEqual(created.card_status, '正常')

    def test_update_type_and_password(self):
        """编辑可改货币类型/开户日期并重置密码，密码同样哈希入库"""
        response = self.manager_client.put(
            f'/api/card/{CARD_ID}/', {
                'cur_type': '美元',
                'open_date': timezone.now().isoformat(),
                'open_money': '500.00',
                'customer_id': self.customer.customer_id,
                'password': 'newpass123',
            }, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self._refresh_card()
        self.assertEqual(self.card.cur_type, '美元')
        self.assertEqual(self.card.balance, Decimal('100.00'))
        self.assertTrue(check_password('newpass123', self.card.password))

    def test_update_cannot_change_balance_status_or_open_money(self):
        """余额、卡状态与开户金额在编辑时均被忽略"""
        response = self.manager_client.put(
            f'/api/card/{CARD_ID}/', {
                'cur_type': '人民币',
                'open_date': timezone.now().isoformat(),
                'open_money': '500.00',
                'balance': '0.00',
                'card_status': '销户',
                'customer_id': self.customer.customer_id,
            }, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self._refresh_card()
        self.assertEqual(self.card.balance, Decimal('100.00'))
        self.assertEqual(self.card.card_status, '正常')
        self.assertEqual(self.card.open_money, Decimal('100.00'))

    def test_update_does_not_require_immutable_fields(self):
        """编辑时不应强制提交不可修改的开户金额与归属客户"""
        response = self.manager_client.put(
            f'/api/card/{CARD_ID}/', {
                'cur_type': '美元',
                'open_date': timezone.now().isoformat(),
            }, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self._refresh_card()
        self.assertEqual(self.card.cur_type, '美元')
        self.assertEqual(self.card.customer_id, self.customer.customer_id)
        self.assertEqual(self.card.open_money, Decimal('100.00'))

    def test_query_officer_cannot_update_card(self):
        response = self.teller_client.put(
            f'/api/card/{CARD_ID}/', self._create_card_payload(self.customer.customer_id), format='json'
        )
        self.assertEqual(response.status_code, 403)
        self._refresh_card()
        self.assertEqual(self.card.cur_type, '人民币')

    def test_unlock_rejected_when_not_lost(self):
        response = self.manager_client.post(f'/api/card/{CARD_ID}/unlock/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        self._refresh_card()
        self.assertEqual(self.card.card_status, '正常')

    def test_closed_card_cannot_change_status(self):
        """销户后挂失/解挂/再次销卡都应被拒绝"""
        self.card.balance = Decimal('0.00')
        self.card.card_status = '销户'
        self.card.save(update_fields=['balance', 'card_status'])

        for action in ('report-loss', 'unlock', 'close'):
            response = self.manager_client.post(f'/api/card/{CARD_ID}/{action}/', {}, format='json')
            self.assertEqual(response.status_code, 400, msg=action)
        self._refresh_card()
        self.assertEqual(self.card.card_status, '销户')
