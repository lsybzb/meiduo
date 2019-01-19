from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
# Create your views here.

# /sms_codes/(?P<mobile>1[3-9]\d{9})/
class SMSCodeView(APIView):
    """
    向手机发送验证码
    """
    def get(self, request, mobile):

        return Response({'手机号': mobile},status=status.HTTP_200_OK)