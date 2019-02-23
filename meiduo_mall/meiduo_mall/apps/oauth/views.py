from django.shortcuts import render
from QQLoginTool.QQtool import OAuthQQ
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from django.conf import settings
import logging

from rest_framework_jwt.settings import api_settings

from carts.utils import merge_cart_cookie_to_redis
from oauth.models import OAuthQQUser
from .serializers import QQAuthUserSerializer
from .utils import generate_save_user_token

# Create your views here.

logger = logging.getLogger('django')


class QQAuthURLView(APIView):
    """获取QQ登陆界面url"""

    def get(self, request):
        next = request.query_params.get('next')
        if not next:
            next = '/'  # 这种操作有什么用?

        # 初始化
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)
        login_url = oauth.get_qq_url()

        return Response({'login_url': login_url})


class QQAuthUserView(GenericAPIView):
    """
    获取用户openid
    1.通过get请求方式获取Authorization Code与state的状态值
    2.通过Authorization Code获取access token
    3.通过access token获取openid
    4.通过openid查询数据库,看是否已经存在
    5.如果不存在,则返回绑定账号的界面,并先将数据加密后返回给前端保存
    6.如果存在,则直接发放jwt令牌,重定向到state存储的页面或首页
    """
    serializer_class = QQAuthUserSerializer

    def get(self, request):
        """获取Authorization Code"""

        auth_code = request.query_params.get('code')

        # SDK初始化
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)
        try:
            access_token = oauth.get_access_token(auth_code)

            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return Response({'message': "QQ服务器错误"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 4.通过openid查询数据库,看是否已经存在
        try:
            auth_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 5.如果不存在,则返回绑定账号的界面,并先将数据加密后返回给前端保存,通过post函数处理
            access_token_openid = generate_save_user_token(openid)
            return Response({"access_token": access_token_openid})
        else:
            # 6.如果存在,则直接发放jwt令牌,重定向到state存储的页面或首页
            # 引用载荷处理函数
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            # 引用签名处理函数
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            # 7.通过关联对象获取user
            user = auth_user.user
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            # 8.构造返回数据
            response = Response({
                "token": token,
                "user_id": user.id,
                "username": user.username
            })

            # 合并购物车
            response = merge_cart_cookie_to_redis(request, user, response)
            return response

    def post(self, request, *args, **kwargs):
        """
        1.提取前端传来的参数
        2.获取序列化器对象,传入需要反序列化的参数
        3.开启校验
        4.保存校验结果,返回的是保存好的user对象
        5.生成jwt令牌
        6.构造响应对象并返回
        """
        serializer = QQAuthUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 5.生成jwt令牌

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        response = Response({
            'token': token,
            'username': user.username,
            'user_id': user.id
        })
        # 做cookie购物车合并到redis操作
        merge_cart_cookie_to_redis(request, user, response)

        return response
