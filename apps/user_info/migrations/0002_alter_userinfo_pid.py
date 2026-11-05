from django.db import migrations, models


def _has_unique_on(cursor, table, column):
    """检查表上是否已存在覆盖该列的唯一索引（避免在既有库重复建索引）"""
    cursor.execute(
        """
        SELECT GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS cols
        FROM information_schema.statistics
        WHERE table_schema = DATABASE() AND table_name = %s AND non_unique = 0
        GROUP BY INDEX_NAME
        """,
        [table],
    )
    return any(row[0] == column for row in cursor.fetchall())


def ensure_pid_unique(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        if _has_unique_on(cursor, 'user_info', 'pid'):
            return
    schema_editor.execute("ALTER TABLE `user_info` ADD UNIQUE KEY `uk_user_info_pid` (`pid`)")


class Migration(migrations.Migration):

    # MySQL 的 DDL 无法回滚，必须关闭迁移级别的原子事务
    atomic = False

    dependencies = [
        ('user_info', '0001_initial'),
    ]

    operations = [
        # 模型层同步唯一约束；库中已存在的唯一索引不会被重复创建
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='userinfo',
                    name='pid',
                    field=models.CharField(db_comment='身份证号，必填且唯一', max_length=18, unique=True),
                ),
            ],
            database_operations=[
                migrations.RunPython(ensure_pid_unique, migrations.RunPython.noop),
            ],
        ),
    ]
