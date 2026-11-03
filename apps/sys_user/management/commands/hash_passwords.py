import re

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.card_info.models import CardInfo
from apps.sys_user.models import SysUser

# Django 各个 hasher 生成的摘要都以固定前缀开头，用于识别“已经是哈希”的值。
# 注意不能用 is_password_usable：它只判断是否为 None 或以 "!" 开头，明文也会返回 True。
HASH_PREFIXES = (
    'pbkdf2_sha256$',
    'pbkdf2_sha1$',
    'argon2',
    'bcrypt$',
    'bcrypt_sha256$',
    'scrypt$',
    'sha1$',
    'md5$',
)
BCRYPT_PREFIXES = ('$2a$', '$2b$', '$2y$')
UNSALTED_MD5_RE = re.compile(r'^[0-9a-fA-F]{32}$')


def looks_hashed(value):
    """值为空或已是哈希摘要返回 True；看起来像明文返回 False"""
    if not value:
        return True
    if value.startswith(HASH_PREFIXES) or value.startswith(BCRYPT_PREFIXES):
        return True
    return bool(UNSALTED_MD5_RE.match(value))


class Command(BaseCommand):
    help = '一次性迁移：把 sys_user、card_info 中遗留的明文密码批量改为 Django 哈希'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只统计需要加密的记录数，不写入数据库',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        targets = (
            (SysUser, 'sys_user'),
            (CardInfo, 'card_info'),
        )

        for model, table_name in targets:
            converted = 0
            skipped = 0
            with transaction.atomic():
                for obj in model.objects.all().iterator():
                    raw_password = obj.password
                    if looks_hashed(raw_password):
                        skipped += 1
                        continue
                    if not dry_run:
                        obj.password = make_password(raw_password)
                        obj.save(update_fields=['password'])
                    converted += 1

            prefix = '[预演] ' if dry_run else ''
            self.stdout.write(
                f'{prefix}{table_name}：{converted} 条明文待加密，{skipped} 条已是哈希或为空，跳过'
            )
