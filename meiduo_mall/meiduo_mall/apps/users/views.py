from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.generics import RetrieveAPIView
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


class UserDetailView(RetrieveAPIView):
    """用户中心视图"""


    # 指定序列化器
    serializer_class = serializers.UserDetailSerializer
    # 指定认证类型
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

