from django.db import models


class TradeInfo(models.Model):
    tid = models.AutoField(primary_key=True, db_comment='交易编号（标识列），从1开始，主键')
    trans_type = models.CharField(max_length=50, db_comment='交易类型，必填')
    card_id = models.CharField(max_length=20, db_comment='银行卡号，必填')
    to_card_id = models.CharField(
        max_length=20, blank=True, null=True, db_comment='对方银行卡号，仅转账流水使用'
    )
    trans_date = models.DateTimeField(db_comment='交易日期，必填')
    trans_money = models.DecimalField(max_digits=18, decimal_places=2, db_comment='交易金额，必填')
    remark = models.CharField(max_length=200, blank=True, null=True, db_comment='备注，非必填')

    class Meta:
        managed = False
        db_table = 'trade_info'
        db_table_comment = '交易信息表'
