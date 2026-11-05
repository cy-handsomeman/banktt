from django.db import migrations


def _has_unique_on(cursor, table, columns):
    cursor.execute(
        """
        SELECT GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS cols
        FROM information_schema.statistics
        WHERE table_schema = DATABASE() AND table_name = %s AND non_unique = 0
        GROUP BY INDEX_NAME
        """,
        [table],
    )
    expected = ','.join(columns)
    return any(row[0] == expected for row in cursor.fetchall())


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
    """把 SQL 脚本里已有的唯一约束与外键同步到迁移，保证全新库也能得到同样的结构"""
    with schema_editor.connection.cursor() as cursor:
        if not _has_unique_on(cursor, 'sys_role_menu', ['role_id', 'menu_id']):
            schema_editor.execute(
                "ALTER TABLE `sys_role_menu` "
                "ADD UNIQUE KEY `uk_role_menu` (`role_id`, `menu_id`)"
            )
        if not _has_foreign_key(cursor, 'sys_role_menu', 'role_id'):
            schema_editor.execute(
                "ALTER TABLE `sys_role_menu` ADD CONSTRAINT `fk_role_menu_role` "
                "FOREIGN KEY (`role_id`) REFERENCES `sys_role` (`role_id`) ON DELETE RESTRICT"
            )
        if not _has_foreign_key(cursor, 'sys_role_menu', 'menu_id'):
            schema_editor.execute(
                "ALTER TABLE `sys_role_menu` ADD CONSTRAINT `fk_role_menu_menu` "
                "FOREIGN KEY (`menu_id`) REFERENCES `sys_menu` (`menu_id`) ON DELETE RESTRICT"
            )


class Migration(migrations.Migration):

    # MySQL 的 DDL 无法回滚，必须关闭迁移级别的原子事务
    atomic = False

    dependencies = [
        ('sys_role_menu', '0001_initial'),
        ('sys_role', '0001_initial'),
        ('sys_menu', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterUniqueTogether(
                    name='sysrolemenu',
                    unique_together={('role_id', 'menu_id')},
                ),
            ],
            database_operations=[
                migrations.RunPython(sync_constraints, migrations.RunPython.noop),
            ],
        ),
    ]
