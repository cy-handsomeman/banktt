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
        if _has_foreign_key(cursor, 'card_info', 'customer_id'):
            return
    schema_editor.execute(
        "ALTER TABLE `card_info` ADD CONSTRAINT `fk_card_customer` "
        "FOREIGN KEY (`customer_id`) REFERENCES `user_info` (`customer_id`) ON DELETE RESTRICT"
    )


class Migration(migrations.Migration):

    # MySQL 的 DDL 无法回滚，必须关闭迁移级别的原子事务
    atomic = False

    dependencies = [
        ('card_info', '0001_initial'),
        ('user_info', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(sync_constraints, migrations.RunPython.noop),
    ]
