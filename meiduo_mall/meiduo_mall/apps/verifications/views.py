from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from random import randint
from django_redis import get_redis_connection
import logging


from . import constants
from celery_tasks.sms import tasks as sms_tasks

# 日志生成器
logger = logging.getLogger('django')


# Create your views here.

# /sms_codes/(?P<mobile>1[3-9]\d{9})/
class SMSCodeView(GenericAPIView):
    """
    向手机发送验证码
    """

    def get(self, request, mobile):
        """
        1.创建redis连接
        2.检查是否60秒内已发送过验证码
        3.生成短信验证码
        4.生成已经发送验证码的标志
        5.把验证码与发送标志存储到redis中
        6.利用容联云通讯发短信
        :param request: 请求对象
        :param mobile: 手机号
        :return: 返回成功或失败
        """

        # 1.创建redis连接
        redis_conn = get_redis_connection()

        # 2.检查是否60秒内已发送过验证码,
        send_flag = redis_conn.get('sms_flag_%s' % mobile)

        if send_flag:
            return Response({"message": "发送验证码过于频繁"}, status.HTTP_400_BAD_REQUEST)

        # 3.生成短信验证码,并在控制台输出
        sms_cdoe = "%06d" % randint(0, 999999)
        logger.debug(sms_cdoe)

        # 4.把验证码与发送标志存入redis
        pl = redis_conn.pipeline()
        pl.setex('sms_code_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_cdoe)
        pl.setex('sms_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()

        # 4.利用容联云通讯发短信
        # CCP().send_template_sms(mobile, [sms_cdoe, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)

        sms_code_expires = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
        sms_tasks.send_sms_code.delay(mobile, sms_cdoe, sms_code_expires)

        # 响应发送验证码结果
        return Response({'message': "OK"})
