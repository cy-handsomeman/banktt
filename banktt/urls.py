from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView
from django.shortcuts import render

from apps.sys_user.views import login_log_list
from apps.sys_menu.views import menu_list

def index(request):
    return render(request, 'index.html')

def login(request):
    return render(request, 'login.html')

urlpatterns = [
    path('', index, name='index'),  # 首页直接返回 index.html
    path('login/', login, name='login'),  # 登录页面
    path('user/', include('apps.user_info.urls')),  # user_info 独立首页
    path('card/', include('apps.card_info.urls')),  # card_info 独立首页
    path('trade/', include('apps.trade_info.urls')),  # trade_info 独立首页
    path('role/', include('apps.sys_role.urls')),  # sys_role 独立首页
    path('sys_user/', include('apps.sys_user.urls')),  # sys_user 独立首页
    path('user_role/', include('apps.sys_user_role.urls')),  # sys_user_role 独立首页
    path('menu/', menu_list, name='menu_index'),  # 菜单管理首页
    path('login_log/', login_log_list, name='login_log_index'),  # 登录日志首页
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