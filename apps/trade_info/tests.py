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
    """资金链路回归测试：转账双边记账、余额校验、冲正幂等、余额还原"""

    def setUp(self):
        cache.clear()
        customer = UserInfo.objects.create(
            customer_name='张三', pid='110101199001010011', telephone='13800000000'
        )
        self.card_a = CardInfo.objects.create(
            card_id=CARD_A, cur_type='CNY', open_date=timezone.now(),
            open_money=Decimal('100.00'), balance=Decimal('100.00'), card_status='正常',
            password=make_password('123456'), customer_id=customer.customer_id,
        )
        self.card_b = CardInfo.objects.create(
            card_id=CARD_B, cur_type='CNY', open_date=timezone.now(),
            open_money=Decimal('200.00'), balance=Decimal('200.00'), card_status='正常',
            password=make_password('123456'), customer_id=customer.customer_id,
        )
        self.manager = self._make_user('test_manager', 2)
        self.teller = self._make_user('test_teller', 3)
        self.client.force_authenticate(user=SysUserPrincipal(self.manager))

    @staticmethod
    def _make_user(user_name, role_id):
        user = SysUser.objects.create(
            user_name=user_name, pid='110101199001010022', email='',
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

    def test_reversal_restores_balances_and_cannot_repeat(self):
        self.client.post(
            '/api/trade/',
            {'trans_type': '转账', 'card_id': CARD_A, 'to_card_id': CARD_B, 'trans_money': '50.00'},
            format='json',
        )
        out_trade = TradeInfo.objects.get(trans_type='转账转出')

        response = self.client.post(f'/api/trade/{out_trade.tid}/reverse/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._balance(CARD_A), Decimal('100.00'))
        self.assertEqual(self._balance(CARD_B), Decimal('200.00'))
        self.assertEqual(TradeInfo.objects.filter(trans_type='冲正').count(), 2)
        self.assertTrue(TradeInfo.objects.get(pk=out_trade.tid).is_reversed)

        repeat = self.client.post(f'/api/trade/{out_trade.tid}/reverse/', {}, format='json')
        self.assertEqual(repeat.status_code, 400)
        self.assertEqual(self._balance(CARD_A), Decimal('100.00'))
        self.assertEqual(self._balance(CARD_B), Decimal('200.00'))

    def test_transfer_entry_cannot_be_deleted(self):
        self.client.post(
            '/api/trade/',
            {'trans_type': '转账', 'card_id': CARD_A, 'to_card_id': CARD_B, 'trans_money': '50.00'},
            format='json',
        )
        out_trade = TradeInfo.objects.get(trans_type='转账转出')
        response = self.client.delete(f'/api/trade/{out_trade.tid}/')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(TradeInfo.objects.count(), 2)

    def test_deposit_update_delete_keeps_balance_consistent(self):
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
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(self._balance(CARD_A), Decimal('140.00'))

        deleted = self.client.delete(f'/api/trade/{trade_id}/')
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(self._balance(CARD_A), Decimal('100.00'))

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

    def test_teller_cannot_reverse_trade(self):
        self.client.post(
            '/api/trade/',
            {'trans_type': '转账', 'card_id': CARD_A, 'to_card_id': CARD_B, 'trans_money': '50.00'},
            format='json',
        )
        out_trade = TradeInfo.objects.get(trans_type='转账转出')
        teller_client = APIClient()
        teller_client.force_authenticate(user=SysUserPrincipal(self.teller))
        response = teller_client.post(f'/api/trade/{out_trade.tid}/reverse/', {}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_reversal_rejected_when_card_closed(self):
        """销户卡不能冲正，否则会把余额重新记回已关闭账户"""
        deposit = self.client.post(
            '/api/trade/',
            {'trans_type': '存款', 'card_id': CARD_A, 'trans_money': '50.00'},
            format='json',
        )
        self.assertEqual(deposit.status_code, 201)
        tid = deposit.data['tid']

        withdraw = self.client.post(
            '/api/trade/',
            {'trans_type': '取款', 'card_id': CARD_A, 'trans_money': str(self._balance(CARD_A))},
            format='json',
        )
        self.assertEqual(withdraw.status_code, 201)
        self.assertEqual(self._balance(CARD_A), Decimal('0.00'))

        closed = self.client.post(f'/api/card/{CARD_A}/close/', {}, format='json')
        self.assertEqual(closed.status_code, 200)

        response = self.client.post(f'/api/trade/{tid}/reverse/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('销户', str(response.data.get('detail')))
        self.assertEqual(self._balance(CARD_A), Decimal('0.00'))
