from django.db import models


class CardInfo(models.Model):
    card_id = models.CharField(primary_key=True, max_length=20, db_comment='卡号，主键')
    cur_type = models.CharField(max_length=3, db_comment='货币类型，必填')
    open_date = models.DateTimeField(db_comment='开户日期，必填')
    open_money = models.DecimalField(max_digits=18, decimal_places=2, db_comment='开户金额，必填')
    balance = models.DecimalField(max_digits=18, decimal_places=2, db_comment='余额，必填')
    card_status = models.CharField(
        max_length=10, default='正常', db_comment='卡状态：正常/挂失/销户'
    )
    password = models.CharField(max_length=100, db_comment='密码（加密存储），必填')
    customer_id = models.IntegerField(db_comment='客户编号，外键关联user_info表')

    class Meta:
        managed = False
        db_table = 'card_info'
        db_table_comment = '银行卡信息表'
