from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView
from django.shortcuts import render

from apps.sys_user.views import login_log_list
from apps.user_info.urls import page_urlpatterns as user_page_urlpatterns
from apps.card_info.urls import page_urlpatterns as card_page_urlpatterns
from apps.trade_info.urls import (
    page_urlpatterns as trade_page_urlpatterns,
    records_page_urlpatterns as trade_records_page_urlpatterns,
)
from apps.sys_role.urls import page_urlpatterns as role_page_urlpatterns
from apps.sys_user.urls import page_urlpatterns as sys_user_page_urlpatterns
from banktt.dashboard import dashboard_page, dashboard_summary

def index(request):
    return render(request, 'index.html')

def login(request):
    return render(request, 'login.html')

urlpatterns = [
    path('', index, name='index'),  # 首页直接返回 index.html
    path('login/', login, name='login'),  # 登录页面
    path('dashboard/', dashboard_page, name='dashboard'),  # 运营总览
    path('user/', include(user_page_urlpatterns)),  # user_info 独立首页
    path('card/', include(card_page_urlpatterns)),  # card_info 独立首页
    path('trade/', include(trade_page_urlpatterns)),  # trade_info 独立首页
    path('transactions/', include(trade_records_page_urlpatterns)),  # 交易流水
    path('role/', include(role_page_urlpatterns)),  # sys_role 独立首页
    path('sys_user/', include(sys_user_page_urlpatterns)),  # sys_user 独立首页
    path('login_log/', login_log_list, name='login_log_index'),  # 登录日志首页
    path('api/dashboard/summary/', dashboard_summary, name='dashboard_summary'),
    path('api/', include('apps.user_info.urls')),
    path('api/', include('apps.trade_info.urls')),
    path('api/', include('apps.card_info.urls')),
    path('api/', include('apps.sys_menu.urls')),
    path('api/', include('apps.sys_role.urls')),
    path('api/', include('apps.sys_role_menu.urls')),
    path('api/', include('apps.sys_user.urls')),
    path('api/', include('apps.sys_user_role.urls')),

    # JWT 刷新：refresh 有效期内可换取新的 access
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 新版 API 文档（替换原来的 include_docs_urls）
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)