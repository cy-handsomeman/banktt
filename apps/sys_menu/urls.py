from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.sys_menu.views import SysMenuViewSet

router = DefaultRouter()
router.register('menu', SysMenuViewSet, basename='menu')

urlpatterns = [
    path('', include(router.urls)),
]
