from django.db import models


class SysMenu(models.Model):
    menu_id = models.AutoField(primary_key=True, db_comment='菜单编号（标识列），从1开始，主键')
    menu_name = models.CharField(max_length=100, db_comment='菜单名称，必填')
    menu_url = models.CharField(max_length=200, blank=True, null=True, db_comment='菜单URL，非必填')
    parent_id = models.IntegerField(default=0, db_comment='父菜单ID，默认0表示顶级菜单')
    sort_order = models.IntegerField(default=0, db_comment='排序号，默认0')
    remark = models.CharField(max_length=200, blank=True, null=True, db_comment='备注，非必填')

    class Meta:
        managed = False
        db_table = 'sys_menu'
        db_table_comment = '系统菜单表'
