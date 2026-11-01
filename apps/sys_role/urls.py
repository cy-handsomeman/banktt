from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.sys_role.views import SysRoleViewSet, sys_role_list
from django.shortcuts import render

router = DefaultRouter()
router.register('role', SysRoleViewSet, basename='role')

def sys_role_index(request):
    return render(request, 'sys_role.html')

# 页面路由和API路由分开
page_urlpatterns = [
    path('', sys_role_index, name='sys_role_index'),  # 返回HTML页面
]

api_urlpatterns = [
    path('sys_role_list/', sys_role_list, name='sys_role_list'),
    path('', include(router.urls)),
]

urlpatterns = page_urlpatterns + api_urlpatterns