from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.shortcuts import render

from apps.sys_user.views import SysUserViewSet, SysLoginLogViewSet

router = DefaultRouter()
router.register('sys_user', SysUserViewSet, basename='sys_user')
router.register('login_log', SysLoginLogViewSet, basename='login_log')


def sys_user_index(request):
    return render(request, 'sys_user.html')


# 页面路由（仅在 /sys_user/ 下挂载）与 API 路由（仅在 /api/ 下挂载）分开导出
page_urlpatterns = [
    path('', sys_user_index, name='sys_user_index'),
]

urlpatterns = [
    path('', include(router.urls)),
]
