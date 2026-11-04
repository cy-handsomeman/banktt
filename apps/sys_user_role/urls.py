from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.shortcuts import render

from apps.sys_user_role.views import SysUserRoleViewSet, get_user_menu, check_super_admin

router = DefaultRouter()
router.register('sys_user_role', SysUserRoleViewSet, basename='sys_user_role')


def sys_user_role_index(request):
    return render(request, 'sys_user_role.html')


# 页面路由（仅在 /user_role/ 下挂载）与 API 路由（仅在 /api/ 下挂载）分开导出
page_urlpatterns = [
    path('', sys_user_role_index, name='sys_user_role_index'),
]

urlpatterns = [
    path('get_user_menu/', get_user_menu, name='get_user_menu'),
    path('check_super_admin/', check_super_admin, name='check_super_admin'),
    path('', include(router.urls)),
]
