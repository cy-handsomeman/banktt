from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.shortcuts import render

from apps.user_info.views import UserViewSet

router = DefaultRouter()
router.register('user', UserViewSet, basename='user')


def user_index(request):
    return render(request, 'user_info.html')


# 页面路由（仅在 /user/ 下挂载）与 API 路由（仅在 /api/ 下挂载）分开导出
page_urlpatterns = [
    path('', user_index, name='user_index'),
]

urlpatterns = [
    path('', include(router.urls)),
]
