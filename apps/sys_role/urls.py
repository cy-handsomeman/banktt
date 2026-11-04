from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.shortcuts import render

from apps.sys_role.views import SysRoleViewSet

router = DefaultRouter()
router.register('role', SysRoleViewSet, basename='role')


def sys_role_index(request):
    return render(request, 'sys_role.html')


# 页面路由（仅在 /role/ 下挂载）与 API 路由（仅在 /api/ 下挂载）分开导出
page_urlpatterns = [
    path('', sys_role_index, name='sys_role_index'),
]

urlpatterns = [
    path('', include(router.urls)),
]
