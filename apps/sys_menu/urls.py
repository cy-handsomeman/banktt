from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.sys_menu.views import SysMenuViewSet, menu_list

router = DefaultRouter()
router.register('menu', SysMenuViewSet, basename='menu')

page_urlpatterns = [
    path('', menu_list, name='menu_index'),
]

api_urlpatterns = [
    path('', include(router.urls)),
]

urlpatterns = page_urlpatterns + api_urlpatterns
