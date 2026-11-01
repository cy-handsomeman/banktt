from django.db import models


class SysRoleMenu(models.Model):
    id = models.AutoField(primary_key=True, db_comment='主键ID，自增')
    role_id = models.IntegerField(db_comment='角色ID，关联sys_role表')
    menu_id = models.IntegerField(db_comment='菜单ID，关联sys_menu表')

    class Meta:
        managed = False
        db_table = 'sys_role_menu'
        db_table_comment = '角色菜单关联表'
