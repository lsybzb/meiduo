from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated

from users.models import User
from . import serializers


class UsernameCountView(APIView):
    """获取用户名数量"""

    def get(self, request, username):
        # 查询传入的用户名的数量
        count = User.objects.filter(username=username).count()

        data = {
            'username': username,
            'count': count
        }
        return Response(data)


class MobileCountView(APIView):
    """获取手机数量"""

    def get(self, request, mobile):
        # 查询传入的手机号码的数量
        count = User.objects.filter(mobile=mobile).count()
        # 组织返回数据
        data = {
            'mobile': mobile,
            'count': count
        }
        # 返回数据
        return Response(data)


class CreateUserView(CreateAPIView):
    """创建用户"""
    serializer_class = serializers.CreateUserSerializer

# url(r'^user/$', views.UserDetailView.as_view())
class UserDetailView(RetrieveAPIView):
    """用户中心视图"""


    # 指定序列化器
    serializer_class = serializers.UserDetailSerializer
    # 指定认证类型
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

# url(r'^email/$', views.EmailView.as_view()
class EmailView(UpdateAPIView):
    """保存邮箱"""
    # 指定序列化器
    serializer_class = serializers.EmailSerializer
    # 指定认证类型
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class VerifyEmailView(APIView):
    """验证邮箱"""

    def get(self, request):
        # 获取查询字符串中的token
        token = request.query_params.get('token')
        if not token:
            return Response({"message": "未获取到验证值"}, status=status.HTTP_400_BAD_REQUEST)
        # 解密检查
        user = User.check_email(token)

        if not user:
            return Response({"message": "邮箱验证失败"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.email_active = True
            user.save()
            return Response({"message": "OK"})