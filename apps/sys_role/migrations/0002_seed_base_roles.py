from django.db import migrations

# 与 apps/sys_user/permissions.py 中的角色常量保持一致
BASE_ROLES = (
    (1, '超管', '系统超级管理员，拥有全部权限'),
    (2, '大堂经理', '可办理销卡、冲正与删除类业务'),
    (3, '银行柜员', '可办理日常柜面业务'),
)


def seed_base_roles(apps, schema_editor):
    """写入系统内置角色：外键约束与权限常量都依赖这三个角色必须存在"""
    SysRole = apps.get_model('sys_role', 'SysRole')
    for role_id, role_name, description in BASE_ROLES:
        SysRole.objects.get_or_create(
            role_id=role_id,
            defaults={'role_name': role_name, 'description': description},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('sys_role', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_base_roles, migrations.RunPython.noop),
    ]
