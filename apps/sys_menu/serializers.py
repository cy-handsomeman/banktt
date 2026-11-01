from rest_framework import serializers
from apps.sys_menu.models import SysMenu


class SysMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysMenu
        fields = '__all__'
