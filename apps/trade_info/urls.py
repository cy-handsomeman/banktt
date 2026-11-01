from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.trade_info.views import TradeInfoViewSet, trade_info_list
from django.shortcuts import render

router = DefaultRouter()
router.register('trade', TradeInfoViewSet, basename='trade')

def trade_index(request):
    return render(request, 'trade_info.html')

# 页面路由和API路由分开
page_urlpatterns = [
    path('', trade_index, name='trade_index'),  # 返回HTML页面
]

api_urlpatterns = [
    path('trade_info_list/', trade_info_list, name='trade_info_list'),
    path('', include(router.urls)),
]

urlpatterns = page_urlpatterns + api_urlpatterns