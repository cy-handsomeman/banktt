from django.shortcuts import render
from rest_framework import viewsets, status  # 需要添加 status
from rest_framework.response import Response  # 需要添加 Response
from rest_framework.decorators import action
from apps.sys_user.models import SysUser
from apps.sys_user.serializers import SysUserSerializer


def sys_user_list(request):
    users = SysUser.objects.all()
    return render(request, 'sys_user.html', {'users': users})


class SysUserViewSet(viewsets.ModelViewSet):
    queryset = SysUser.objects.all().order_by('create_time')
    serializer_class = SysUserSerializer
    filterset_fields = ['user_id', 'user_name', 'mobile', 'pid']
    search_fields = ['user_name', 'mobile', 'pid', 'email', 'address']
    
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """
        登录接口
        """
        userName = request.data.get('userName')
        password = request.data.get('password')
        try:
            if not userName or userName.strip() == '':
                return Response({'message': '用户名不能为空'})
            userQuerySet = SysUser.objects.filter(user_name = userName)
            if userQuerySet:
                user = userQuerySet.first()
                password1 = user.password
                if password == password1:
                    return Response({
                        'message': '登录成功',
                        'user_id': user.user_id,
                        'user_name': user.user_name
                    })
                else:
                    return Response({'message': '密码错误'})
            else:
                return Response({'message': '用户名不存在'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )