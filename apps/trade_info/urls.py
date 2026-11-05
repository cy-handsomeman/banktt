from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.shortcuts import render

from apps.trade_info.views import TradeInfoViewSet

router = DefaultRouter()
router.register('trade', TradeInfoViewSet, basename='trade')


def trade_index(request):
    return render(request, 'trade_info.html')


def trade_records(request):
    return render(request, 'trade_records.html')


# 页面路由（仅在 /trade/ 下挂载）与 API 路由（仅在 /api/ 下挂载）分开导出
page_urlpatterns = [
    path('', trade_index, name='trade_index'),
]

records_page_urlpatterns = [
    path('', trade_records, name='trade_records_index'),
]

urlpatterns = [
    path('', include(router.urls)),
]
