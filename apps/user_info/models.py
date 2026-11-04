from django.db import models # type: ignore

# Create your models here.

class UserInfo(models.Model):
    customer_id = models.AutoField(primary_key=True, db_comment='客户编号（标识列），从1开始，主键')
    customer_name = models.CharField(max_length=100, db_comment='开户名，必填')
    pid = models.CharField(max_length=18, db_comment='身份证号，必填')
    telephone = models.CharField(max_length=20, db_comment='联系电话，必填')
    address = models.CharField(max_length=200, blank=True, null=True, db_comment='居住地址，非必填')

    class Meta:
        managed = True
        db_table = 'user_info'
        db_table_comment = '客户信息表'
