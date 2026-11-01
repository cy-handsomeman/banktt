from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.sys_user.views import SysUserViewSet, sys_user_list
from django.shortcuts import render

router = DefaultRouter()
router.register('sys_user', SysUserViewSet, basename='sys_user')

def sys_user_index(request):
    return render(request, 'sys_user.html')

# 页面路由和API路由分开
page_urlpatterns = [
    path('', sys_user_index, name='sys_user_index'),  # 返回HTML页面
]

api_urlpatterns = [
    path('sys_user_list/', sys_user_list, name='sys_user_list'),
    path('', include(router.urls)),
]

urlpatterns = page_urlpatterns + api_urlpatterns