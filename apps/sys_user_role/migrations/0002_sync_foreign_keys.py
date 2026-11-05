from django.db import migrations


def _has_foreign_key(cursor, table, column):
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.key_column_usage
        WHERE table_schema = DATABASE() AND table_name = %s
          AND column_name = %s AND referenced_table_name IS NOT NULL
        """,
        [table, column],
    )
    return cursor.fetchone()[0] > 0


def sync_constraints(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        if not _has_foreign_key(cursor, 'sys_user_role', 'user_id'):
            schema_editor.execute(
                "ALTER TABLE `sys_user_role` ADD CONSTRAINT `fk_user_role_user` "
                "FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`user_id`) ON DELETE RESTRICT"
            )
        if not _has_foreign_key(cursor, 'sys_user_role', 'role_id'):
            schema_editor.execute(
                "ALTER TABLE `sys_user_role` ADD CONSTRAINT `fk_user_role_role` "
                "FOREIGN KEY (`role_id`) REFERENCES `sys_role` (`role_id`) ON DELETE RESTRICT"
            )


class Migration(migrations.Migration):

    # MySQL 的 DDL 无法回滚，必须关闭迁移级别的原子事务
    atomic = False

    dependencies = [
        ('sys_user_role', '0001_initial'),
        ('sys_user', '0001_initial'),
        ('sys_role', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(sync_constraints, migrations.RunPython.noop),
    ]
