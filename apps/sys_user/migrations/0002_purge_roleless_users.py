"""
清理没有任何角色绑定的历史系统账号及其登录日志。
这些账号无法通过角色获得业务权限，属于历史遗留脏数据；
删除后可保证 sys_user.pid 唯一约束可以安全建立（其余账号身份证号不重复）。
"""

from django.db import migrations


def purge_roleless_users(apps, schema_editor):
    db = schema_editor.connection.alias
    SysUser = apps.get_model('sys_user', 'SysUser')
    SysUserRole = apps.get_model('sys_user_role', 'SysUserRole')
    SysLoginLog = apps.get_model('sys_user', 'SysLoginLog')

    bound_user_ids = set(SysUserRole.objects.using(db).values_list('user_id', flat=True))
    roleless_ids = [
        user_id
        for user_id in SysUser.objects.using(db).values_list('user_id', flat=True)
        if user_id not in bound_user_ids
    ]
    if not roleless_ids:
        return

    SysLoginLog.objects.using(db).filter(user_id__in=roleless_ids).delete()
    SysUser.objects.using(db).filter(user_id__in=roleless_ids).delete()


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('sys_user', '0001_initial'),
        ('sys_user_role', '0002_sync_foreign_keys'),
        ('sys_role', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(purge_roleless_users, migrations.RunPython.noop),
    ]
