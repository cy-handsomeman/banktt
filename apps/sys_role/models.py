from django.db import models


class SysRole(models.Model):
    role_id = models.AutoField(primary_key=True, db_comment='角色编号（标识列），从1开始，主键')
    role_name = models.CharField(max_length=100, db_comment='角色名称，必填')
    description = models.CharField(max_length=200, blank=True, null=True, db_comment='角色描述，非必填')

    class Meta:
        managed = False
        db_table = 'sys_role'
        db_table_comment = '系统角色表'
