from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.user_info.views import UserViewSet, user_info_list
from django.shortcuts import render

router = DefaultRouter()
router.register('user', UserViewSet, basename='user')

def user_index(request):
    return render(request, 'user_info.html')

# 页面路由和API路由分开
page_urlpatterns = [
    path('', user_index, name='user_index'),  # 返回HTML页面
]

api_urlpatterns = [
    path('user_info_list/', user_info_list, name='user_info_list'),
    path('', include(router.urls)),
]

urlpatterns = page_urlpatterns + api_urlpatterns