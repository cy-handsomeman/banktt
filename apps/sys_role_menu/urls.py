from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.sys_role_menu.views import SysRoleMenuViewSet

router = DefaultRouter()
router.register('role_menu', SysRoleMenuViewSet, basename='role_menu')

urlpatterns = [
    path('', include(router.urls)),
]
