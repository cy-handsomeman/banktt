from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.sys_user_role.views import SysUserRoleViewSet, sys_user_role_list, get_user_menu, check_super_admin
from django.shortcuts import render

router = DefaultRouter()
router.register('sys_user_role', SysUserRoleViewSet, basename='sys_user_role')

def sys_user_role_index(request):
    return render(request, 'sys_user_role.html')

# 页面路由和API路由分开
page_urlpatterns = [
    path('', sys_user_role_index, name='sys_user_role_index'),  # 返回HTML页面
]

api_urlpatterns = [
    path('sys_user_role_list/', sys_user_role_list, name='sys_user_role_list'),
    path('get_user_menu/', get_user_menu, name='get_user_menu'),
    path('check_super_admin/', check_super_admin, name='check_super_admin'),
    path('', include(router.urls)),
]

urlpatterns = page_urlpatterns + api_urlpatterns