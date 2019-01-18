from rest_framework.views import exception_handler as drf_exception_handler
from django.db import DatabaseError
from redis.exceptions import RedisError
import logging
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('django')


def exception_handler(exc, context):
    """自定义异常捕获函数,再DRF基础上添加mysql及redis异常捕获机制"""

    # 获取DRF的异常信息
    response = drf_exception_handler(exc, context)

    if response is None:
        view = context['view']
        if isinstance(exc, DatabaseError) or isinstance(exc, RedisError):
            # 数据库异常
            logger.error("[%s]: %s" % (view, exc))
            response = Response({'message': "服务器内部错误"}, status=status.HTTP_507_INSUFFICIENT_STORAGE)

    return response


