"""
清理不符合新规则的历史客户：
  - 身份证号不是 18 位（末位可为 X）
  - 联系电话不是 11 位手机号
这些客户对应的历史银行卡与交易流水已由 card_info.0003 先行清理，
此处仅删除客户本身，保证后续新数据在格式校验下不会与历史脏数据冲突。
"""

import re

from django.db import migrations


PID_PATTERN = re.compile(r'^\d{17}[\dXx]$')
TELEPHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')


def purge_customers(apps, schema_editor):
    db = schema_editor.connection.alias
    UserInfo = apps.get_model('user_info', 'UserInfo')

    invalid_ids = [
        customer_id
        for customer_id, pid, telephone in UserInfo.objects.using(db).values_list(
            'customer_id', 'pid', 'telephone'
        )
        if not PID_PATTERN.fullmatch(pid or '')
        or not TELEPHONE_PATTERN.fullmatch(telephone or '')
    ]
    if invalid_ids:
        UserInfo.objects.using(db).filter(customer_id__in=invalid_ids).delete()


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('user_info', '0002_alter_userinfo_pid'),
        ('card_info', '0003_purge_invalid_cards'),
    ]

    operations = [
        migrations.RunPython(purge_customers, migrations.RunPython.noop),
    ]
