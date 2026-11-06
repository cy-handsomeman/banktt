"""
清理不符合新规则的历史银行卡：
  - 卡号不是 622202 开头的 16 位数字（历史手工录入数据）
  - 归属客户不存在或客户本身已不合规（身份证/电话格式非法）
同时删除这些卡关联的交易流水（外键 RESTRICT 要求先删流水），
并把存量货币代码 RMB 统一迁移为界面枚举“人民币”。
"""

import re

from django.db import migrations


CARD_ID_PATTERN = re.compile(r'^622202\d{10}$')
PID_PATTERN = re.compile(r'^\d{17}[\dXx]$')
TELEPHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')


def _valid_customer_ids(UserInfo, db):
    return {
        customer_id
        for customer_id, pid, telephone in UserInfo.objects.using(db).values_list(
            'customer_id', 'pid', 'telephone'
        )
        if PID_PATTERN.fullmatch(pid or '') and TELEPHONE_PATTERN.fullmatch(telephone or '')
    }


def purge_cards(apps, schema_editor):
    db = schema_editor.connection.alias
    UserInfo = apps.get_model('user_info', 'UserInfo')
    CardInfo = apps.get_model('card_info', 'CardInfo')
    TradeInfo = apps.get_model('trade_info', 'TradeInfo')

    valid_customers = _valid_customer_ids(UserInfo, db)
    invalid_card_ids = [
        card_id
        for card_id, customer_id in CardInfo.objects.using(db).values_list('card_id', 'customer_id')
        if not CARD_ID_PATTERN.fullmatch(card_id or '') or customer_id not in valid_customers
    ]
    if invalid_card_ids:
        TradeInfo.objects.using(db).filter(card_id__in=invalid_card_ids).delete()
        CardInfo.objects.using(db).filter(card_id__in=invalid_card_ids).delete()

    CardInfo.objects.using(db).filter(cur_type='RMB').update(cur_type='人民币')


class Migration(migrations.Migration):

    # 跨表删除涉及外键约束，交给数据库逐条校验即可，无需整体事务
    atomic = False

    dependencies = [
        ('card_info', '0002_sync_foreign_keys'),
        ('trade_info', '0002_sync_foreign_keys'),
        ('user_info', '0002_alter_userinfo_pid'),
    ]

    operations = [
        migrations.RunPython(purge_cards, migrations.RunPython.noop),
    ]
