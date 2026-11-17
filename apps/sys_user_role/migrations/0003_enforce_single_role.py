from django.db import migrations

# 管理员角色编号（与 settings.SUPER_ADMIN_ROLE_ID 默认值一致）
# 迁移内不引用运行时代码，避免后续配置调整影响历史迁移结果
SUPER_ADMIN_ROLE_ID = 1


def collapse_to_single_role(apps, schema_editor):
    """把存量多角色用户收敛为单一角色：管理员优先，其次 role_id 最小"""
    SysUserRole = apps.get_model('sys_user_role', 'SysUserRole')
    db = schema_editor.connection.alias

    bindings = {}
    for binding in SysUserRole.objects.using(db).all().order_by('user_id', 'role_id', 'id'):
        bindings.setdefault(binding.user_id, []).append(binding)

    for user_id, items in bindings.items():
        if len(items) <= 1:
            continue
        # 管理员优先；否则保留 role_id 最小的那条（items 已按 role_id 升序）
        keep = next(
            (item for item in items if item.role_id == SUPER_ADMIN_ROLE_ID),
            items[0],
        )
        stale_ids = [item.pk for item in items if item.pk != keep.pk]
        SysUserRole.objects.using(db).filter(pk__in=stale_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('sys_user_role', '0002_sync_foreign_keys'),
    ]

    operations = [
        migrations.RunPython(collapse_to_single_role, migrations.RunPython.noop),
    ]
