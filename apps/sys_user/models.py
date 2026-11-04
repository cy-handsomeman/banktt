from django.db import models


class SysUser(models.Model):
    user_id = models.AutoField(primary_key=True, db_comment='用户编号（标识列），从1开始，主键')
    user_name = models.CharField(max_length=100, unique=True, db_comment='用户名，必填且唯一')
    pid = models.CharField(max_length=18, db_comment='身份证号，必填')
    email = models.CharField(max_length=100, blank=True, null=True, db_comment='邮箱，非必填')
    mobile = models.CharField(max_length=20, db_comment='手机号，必填')
    address = models.CharField(max_length=200, blank=True, null=True, db_comment='地址，非必填')
    password = models.CharField(max_length=100, db_comment='密码（加密存储），必填')
    create_time = models.DateTimeField(auto_now_add=True, db_comment='创建时间，必填')
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, db_comment='更新时间，非必填')

    class Meta:
        managed = False
        db_table = 'sys_user'
        db_table_comment = '系统用户表'


class SysLoginLog(models.Model):
    """登录日志（含成功与失败），用于安全审计"""

    id = models.AutoField(primary_key=True, db_comment='日志ID')
    user_id = models.IntegerField(blank=True, null=True, db_comment='用户编号')
    user_name = models.CharField(
        max_length=100, blank=True, null=True, db_comment='登录用户名'
    )
    login_ip = models.CharField(max_length=64, blank=True, null=True, db_comment='登录IP')
    user_agent = models.CharField(
        max_length=255, blank=True, null=True, db_comment='浏览器标识'
    )
    status = models.CharField(max_length=10, db_comment='结果：成功/失败')
    message = models.CharField(max_length=200, blank=True, null=True, db_comment='说明')
    login_time = models.DateTimeField(db_comment='登录时间')

    class Meta:
        managed = False
        db_table = 'sys_login_log'
        db_table_comment = '登录日志表'
