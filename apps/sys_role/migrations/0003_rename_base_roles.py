from django.db import migrations

# 角色 ID 与 apps/sys_user/permissions.py 中的常量保持一致
RENAMED_ROLES = (
    (1, '管理员', '系统管理员，拥有全部功能与系统管理权限'),
    (2, '柜员', '办理客户、银行卡与柜面交易业务'),
    (3, '查询员', '只读查看客户、银行卡与交易流水'),
)


def rename_base_roles(apps, schema_editor):
    """把内置角色改名为新版本的三类角色，重复执行结果一致"""
    SysRole = apps.get_model('sys_role', 'SysRole')
    for role_id, role_name, description in RENAMED_ROLES:
        SysRole.objects.filter(role_id=role_id).update(
            role_name=role_name,
            description=description,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('sys_role', '0002_seed_base_roles'),
    ]

    operations = [
        migrations.RunPython(rename_base_roles, migrations.RunPython.noop),
    ]
