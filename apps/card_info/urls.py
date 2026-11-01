from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.card_info.views import CardInfoViewSet, card_info_list
from django.shortcuts import render

router = DefaultRouter()
router.register('card', CardInfoViewSet, basename='card')

def card_index(request):
    return render(request, 'card_info.html')

# 页面路由和API路由分开
page_urlpatterns = [
    path('', card_index, name='card_index'),  # 返回HTML页面
]

api_urlpatterns = [
    path('card_info_list/', card_info_list, name='card_info_list'),
    path('', include(router.urls)),
]

urlpatterns = page_urlpatterns + api_urlpatterns