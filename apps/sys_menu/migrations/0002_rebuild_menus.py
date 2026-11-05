from django.db import migrations

# (menu_url, menu_name, menu_group, icon, sort_order)
TARGET_MENUS = (
    ('/dashboard/', '运营总览', '工作台', 'fas fa-chart-pie', 1),
    ('/user/', '客户管理', '柜面业务', 'fas fa-users', 2),
    ('/card/', '银行卡管理', '柜面业务', 'fas fa-credit-card', 3),
    ('/trade/', '柜面业务', '柜面业务', 'fas fa-exchange-alt', 4),
    ('/transactions/', '交易流水', '柜面业务', 'fas fa-list-alt', 5),
    ('/sys_user/', '用户管理', '系统管理', 'fas fa-user-cog', 6),
    ('/role/', '角色与权限', '系统管理', 'fas fa-shield-alt', 7),
    ('/login_log/', '登录日志', '系统管理', 'fas fa-history', 8),
)

# 角色授权：管理员全部，柜员可办理业务，查询员只读
ROLE_MENU_URLS = {
    1: {item[0] for item in TARGET_MENUS},
    2: {'/dashboard/', '/user/', '/card/', '/trade/', '/transactions/'},
    3: {'/dashboard/', '/user/', '/card/', '/transactions/'},
}


def rebuild_menus(apps, schema_editor):
    """按新导航重建菜单与角色授权，重复执行结果一致"""
    SysMenu = apps.get_model('sys_menu', 'SysMenu')
    SysRoleMenu = apps.get_model('sys_role_menu', 'SysRoleMenu')

    keep_urls = [item[0] for item in TARGET_MENUS]

    # 删除新导航之外的菜单（菜单管理、用户角色关联等）及其授权
    stale_ids = list(
        SysMenu.objects.exclude(menu_url__in=keep_urls).values_list('menu_id', flat=True)
    )
    if stale_ids:
        SysRoleMenu.objects.filter(menu_id__in=stale_ids).delete()
        SysMenu.objects.filter(menu_id__in=stale_ids).delete()

    url_to_id = {}
    for url, menu_name, menu_group, icon, sort_order in TARGET_MENUS:
        # 同一 URL 只保留最早的一条，避免历史重复数据让导航出现重复项
        rows = list(SysMenu.objects.filter(menu_url=url).order_by('menu_id'))
        if rows:
            menu = rows[0]
            duplicate_ids = [row.menu_id for row in rows[1:]]
            if duplicate_ids:
                SysRoleMenu.objects.filter(menu_id__in=duplicate_ids).delete()
                SysMenu.objects.filter(menu_id__in=duplicate_ids).delete()
            menu.menu_name = menu_name
            menu.menu_group = menu_group
            menu.icon = icon
            menu.sort_order = sort_order
            menu.parent_id = 0
            menu.save(update_fields=['menu_name', 'menu_group', 'icon', 'sort_order', 'parent_id'])
        else:
            menu = SysMenu.objects.create(
                menu_name=menu_name,
                menu_url=url,
                icon=icon,
                menu_group=menu_group,
                parent_id=0,
                sort_order=sort_order,
            )
        url_to_id[url] = menu.menu_id

    # 重建内置角色授权：先清空再按规格写入，避免残留旧菜单授权
    for role_id, urls in ROLE_MENU_URLS.items():
        SysRoleMenu.objects.filter(role_id=role_id).delete()
        for url in sorted(urls):
            SysRoleMenu.objects.get_or_create(role_id=role_id, menu_id=url_to_id[url])


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('sys_menu', '0001_initial'),
        ('sys_role', '0003_rename_base_roles'),
        ('sys_role_menu', '0002_alter_sysrolemenu_unique_together'),
    ]

    operations = [
        migrations.RunPython(rebuild_menus, migrations.RunPython.noop),
    ]
