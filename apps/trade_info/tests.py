from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.card_info.models import CardInfo
from apps.sys_user.authentication import SysUserPrincipal
from apps.sys_user.models import SysUser
from apps.sys_user_role.models import SysUserRole
from apps.trade_info.models import TradeInfo
from apps.user_info.models import UserInfo

CARD_A = '6222020000000001'
CARD_B = '6222020000000002'


class FundFlowTests(APITestCase):
    """资金链路回归测试：转账双边记账、余额校验、只读角色写拦截"""

    def setUp(self):
        cache.clear()
        customer = UserInfo.objects.create(
            customer_name='张三', pid='110101199001010011', telephone='13800000000'
        )
        self.card_a = CardInfo.objects.create(
            card_id=CARD_A, cur_type='人民币', open_date=timezone.now(),
            open_money=Decimal('100.00'), balance=Decimal('100.00'), card_status='正常',
            password=make_password('123456'), customer_id=customer.customer_id,
        )
        self.card_b = CardInfo.objects.create(
            card_id=CARD_B, cur_type='人民币', open_date=timezone.now(),
            open_money=Decimal('200.00'), balance=Decimal('200.00'), card_status='正常',
            password=make_password('123456'), customer_id=customer.customer_id,
        )
        self.manager = self._make_user('test_manager', 2)
        self.query_officer = self._make_user('test_teller', 3)
        self.client.force_authenticate(user=SysUserPrincipal(self.manager))

    @staticmethod
    def _make_user(user_name, role_id):
        user = SysUser.objects.create(
            user_name=user_name, pid=f'11010119900101{role_id:04d}', email='',
            mobile='13900000000', password=make_password('Test@12345'),
        )
        SysUserRole.objects.create(user_id=user.user_id, role_id=role_id)
        return user

    def _balance(self, card_id):
        return CardInfo.objects.get(card_id=card_id).balance

    def test_transfer_creates_paired_entries_and_moves_balance(self):
        response = self.client.post(
            '/api/trade/',
            {'trans_type': '转账', 'card_id': CARD_A, 'to_card_id': CARD_B, 'trans_money': '50.00'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)

        out_trade = TradeInfo.objects.get(trans_type='转账转出')
        in_trade = TradeInfo.objects.get(trans_type='转账转入')
        self.assertEqual(out_trade.card_id, CARD_A)
        self.assertEqual(in_trade.card_id, CARD_B)
        self.assertEqual(out_trade.pair_tid, in_trade.tid)
        self.assertEqual(in_trade.pair_tid, out_trade.tid)
        self.assertEqual(self._balance(CARD_A), Decimal('50.00'))
        self.assertEqual(self._balance(CARD_B), Decimal('250.00'))

    def test_transfer_rejected_when_balance_insufficient(self):
        response = self.client.post(
            '/api/trade/',
            {'trans_type': '转账', 'card_id': CARD_A, 'to_card_id': CARD_B, 'trans_money': '150.00'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._balance(CARD_A), Decimal('100.00'))
        self.assertEqual(self._balance(CARD_B), Decimal('200.00'))
        self.assertEqual(TradeInfo.objects.count(), 0)

    def test_query_officer_can_read_but_cannot_create_trade(self):
        read_client = APIClient()
        read_client.force_authenticate(user=SysUserPrincipal(self.query_officer))

        listed = read_client.get('/api/trade/')
        self.assertEqual(listed.status_code, 200)

        created = read_client.post(
            '/api/trade/',
            {'trans_type': '存款', 'card_id': CARD_A, 'trans_money': '10.00'},
            format='json',
        )
        self.assertEqual(created.status_code, 403)
        self.assertEqual(self._balance(CARD_A), Decimal('100.00'))

    def test_trade_cannot_be_updated_or_deleted(self):
        self.client.post(
            '/api/trade/',
            {'trans_type': '转账', 'card_id': CARD_A, 'to_card_id': CARD_B, 'trans_money': '50.00'},
            format='json',
        )
        out_trade = TradeInfo.objects.get(trans_type='转账转出')
        updated = self.client.put(
            f'/api/trade/{out_trade.tid}/',
            {'trans_type': '转账', 'card_id': CARD_A, 'trans_money': '60.00'},
            format='json',
        )
        self.assertEqual(updated.status_code, 405)
        deleted = self.client.delete(f'/api/trade/{out_trade.tid}/')
        self.assertEqual(deleted.status_code, 405)
        self.assertEqual(TradeInfo.objects.count(), 2)
        self.assertEqual(self._balance(CARD_A), Decimal('50.00'))
        self.assertEqual(self._balance(CARD_B), Decimal('250.00'))

    def test_deposit_creates_entry_and_keeps_balance_consistent(self):
        created = self.client.post(
            '/api/trade/',
            {'trans_type': '存款', 'card_id': CARD_A, 'trans_money': '30.00'},
            format='json',
        )
        self.assertEqual(created.status_code, 201)
        trade_id = TradeInfo.objects.get(trans_type='存款').tid
        self.assertEqual(self._balance(CARD_A), Decimal('130.00'))

        updated = self.client.put(
            f'/api/trade/{trade_id}/',
            {'trans_type': '存款', 'card_id': CARD_A, 'trans_money': '40.00'},
            format='json',
        )
        self.assertEqual(updated.status_code, 405)
        deleted = self.client.delete(f'/api/trade/{trade_id}/')
        self.assertEqual(deleted.status_code, 405)
        self.assertEqual(self._balance(CARD_A), Decimal('130.00'))

    def test_deposit_into_zero_balance_card(self):
        self.card_a.balance = Decimal('0.00')
        self.card_a.save(update_fields=['balance'])
        response = self.client.post(
            '/api/trade/',
            {'trans_type': '存款', 'card_id': CARD_A, 'trans_money': '10.00'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self._balance(CARD_A), Decimal('10.00'))

    def test_date_range_filter_matches_today(self):
        """日期范围筛选：今日创建的交易必须能被今日区间命中（MySQL 无时区表也不受影响）"""
        self.client.post(
            '/api/trade/',
            {'trans_type': '存款', 'card_id': CARD_A, 'trans_money': '20.00'},
            format='json',
        )
        today = timezone.localdate().isoformat()
        response = self.client.get(f'/api/trade/?start_date={today}&end_date={today}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['trans_type'], '存款')

        past = (timezone.localdate() - timedelta(days=3)).isoformat()
        response = self.client.get(f'/api/trade/?start_date={past}&end_date={past}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
