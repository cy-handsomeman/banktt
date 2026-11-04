from django.db import models


class SysUserRole(models.Model):
    id = models.AutoField(primary_key=True, db_comment='主键ID，自增')
    user_id = models.IntegerField(db_comment='用户ID，关联sys_user表')
    role_id = models.IntegerField(db_comment='角色ID，关联sys_role表')

    class Meta:
        managed = True
        db_table = 'sys_user_role'
        db_table_comment = '用户角色关联表'
        unique_together = ('user_id', 'role_id')  # 防止重复关联
