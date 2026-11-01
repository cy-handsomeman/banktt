from django.shortcuts import render
from rest_framework import viewsets
from apps.user_info.models import UserInfo
from apps.user_info.serializers import UserSerializer


def user_info_list(request):
    return render(request, 'user_info.html')


class UserViewSet(viewsets.ModelViewSet):
    queryset = UserInfo.objects.all()
    serializer_class = UserSerializer