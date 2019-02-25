from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from random import randint
from django_redis import get_redis_connection
import logging


from rest_framework.views import APIView

from meiduo_mall.celery_tasks.email import tasks as sms_tasks
from meiduo_mall.meiduo_mall.utils.captcha.captcha import captcha
from . import constants


# 日志生成器
logger = logging.getLogger('django')


# Create your views here.


class ImageCodeView(APIView):
    """发送图片验证码"""

    def get(self, request, image_code_id):
        # 创建连接到redis的对象
        redis_conn = get_redis_connection('verify_codes')

        if not image_code_id:
            logger.error("参数不足")
            return Response({'message': '微博服务器异常'}, status=status.HTTP_404_NOT_FOUND)
        image_name, real_image_code, image_data = captcha.generate_captcha()
        # 将code_id作为key将验证码图片的真实值保存到redis数据库,并设置有效时长5分钟
        try:
            redis_conn.setex("CODEID_%s" % image_code_id, 300, real_image_code)
            # print(real_image_code)
        except Exception as error:
            logger.info(error)
            return Response({'message': '验证失败'}, status=status.HTTP_400_BAD_REQUEST)
        # 返回验证码图片数据
        resp = HttpResponse(image_data)
        resp._content_type = 'image/jpg'

        return resp



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
        redis_conn = get_redis_connection('verify_code')
        # 图片验证码验证
        image_code = request.query_params.get('text')
        image_code_id = request.query_params.get('image_code_id')
        real_image_code = redis_conn.get("CODEID_%s" % image_code_id)
        if real_image_code.decode() != image_code:
            return Response({'message':'图片验证错误'},status=status.HTTP_400_BAD_REQUEST)
        # 2.检查是否60秒内已发送过验证码,
        send_flag = redis_conn.get('sms_flag_%s' % mobile)

        if send_flag:
            return Response({"message": "发送验证码过于频繁"}, status.HTTP_400_BAD_REQUEST)

        # 3.生成短信验证码,并在控制台输出
        sms_code = "%06d" % randint(0, 999999)
        logger.info(sms_code)

        # 4.把验证码与发送标志存入redis
        pl = redis_conn.pipeline()
        pl.setex('sms_code_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('sms_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()

        # 4.利用容联云通讯发短信
        # CCP().send_template_sms(mobile, [sms_cdoe, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)

        # 发送短信验证码
        sms_code_expires = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
        sms_tasks.send_sms_code.delay(mobile, sms_code, sms_code_expires)

        # 响应发送验证码结果
        return Response({'message': "OK"})
