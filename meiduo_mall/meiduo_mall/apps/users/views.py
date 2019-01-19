from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User


class UsernameCountView(APIView):
    """获取用户名数量"""

    def get(self, request, username):

        count = User.objects.filter(username=username).count()

        data = {
            'username': username,
            'count': count
        }
        return Response(data)


class MobileCountView(APIView):
    """获取手机数量"""

    def get(self, request, mobile):

        count = User.objects.filter(mobile=mobile).count()

        data = {
            'username': mobile,
            'count': count
        }
        return Response(data)