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

CARD_ID = '6222020000000011'


class CardStatusTests(APITestCase):
    """卡状态机与删除保护回归测试"""

    def setUp(self):
        cache.clear()
        customer = UserInfo.objects.create(
            customer_name='王五', pid='110101199001010033', telephone='13600000000'
        )
        self.card = CardInfo.objects.create(
            card_id=CARD_ID, cur_type='CNY', open_date=timezone.now(),
            open_money=Decimal('100.00'), balance=Decimal('100.00'), card_status='正常',
            password=make_password('123456'), customer_id=customer.customer_id,
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
        response = self.teller_client.post(f'/api/card/{CARD_ID}/report-loss/', {}, format='json')
        self.assertEqual(response.status_code, 200)
        self._refresh_card()
        self.assertEqual(self.card.card_status, '挂失')

        repeat = self.teller_client.post(f'/api/card/{CARD_ID}/report-loss/', {}, format='json')
        self.assertEqual(repeat.status_code, 400)

        unlocked = self.teller_client.post(f'/api/card/{CARD_ID}/unlock/', {}, format='json')
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

    def test_card_with_trades_cannot_be_deleted(self):
        TradeInfo.objects.create(
            trans_type='存款', card_id=CARD_ID, trans_date=timezone.now(),
            trans_money=Decimal('10.00'), balance_after=Decimal('110.00'),
        )
        response = self.manager_client.delete(f'/api/card/{CARD_ID}/')
        self.assertEqual(response.status_code, 400)
        self.assertIsInstance(response.data.get('detail'), str)
        self.assertTrue(CardInfo.objects.filter(card_id=CARD_ID).exists())
