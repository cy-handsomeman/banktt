from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.shortcuts import render

from apps.card_info.views import CardInfoViewSet

router = DefaultRouter()
router.register('card', CardInfoViewSet, basename='card')


def card_index(request):
    return render(request, 'card_info.html')


# 页面路由（仅在 /card/ 下挂载）与 API 路由（仅在 /api/ 下挂载）分开导出
page_urlpatterns = [
    path('', card_index, name='card_index'),
]

urlpatterns = [
    path('', include(router.urls)),
]
