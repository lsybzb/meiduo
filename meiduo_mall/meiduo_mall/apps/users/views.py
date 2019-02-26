from random import randint

from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from django_redis import get_redis_connection
from rest_framework_jwt.views import ObtainJSONWebToken
import logging
from django.http import HttpResponse
from rest_framework_jwt.settings import api_settings

from carts.utils import merge_cart_cookie_to_redis
from goods.models import SKU
from goods.serializers import SKUSerializer
from users import constants
from users.models import User
from users.serializers import AddUserBrowsingHistorySerializer
from . import serializers

# 获取图片验证码的
# from meiduo_mall.apps.verifications import constants
from meiduo_mall.utils.captcha.captcha import captcha
from celery_tasks.sms.tasks import send_sms_code

logger = logging.getLogger('django')


class ResetPasswords(APIView):
    """修改密码"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        # print("进入了修改密码put视图")
        user = self.request.user  # 获取当前登录用户

        data = request.data  # 获取前端请求体中的数据

        old_password = data.get('old_password')  # 取出数据键为old_password

        password = data.get('password')  # 取出数据键为password
        password2 = data.get('password2')  # 取出数据键为password2

        if not user.check_password(old_password):  # 校验原密码是否正确
            return Response({"message": "老铁,密码错啦!"}, status=status.HTTP_403_FORBIDDEN)
        # print("原始密码是否正确")
        if not all([old_password, password, password2]):
            return Response({"message": "参数不足!"}, status=status.HTTP_400_BAD_REQUEST)

        if password != password2:  # 判断新密码和确认密码是否相等
            return Response({"message": "新密码不一致!"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()  # 保存到数据库

        return Response({"message": "ok"})


class ResetPasswordView(APIView):
    # post '/users/' + this.user_id + '/password/'
    def post(self, request, user_id):
        # 1 获取参数： 两次密码
        password = request.data.get("password")
        password2 = request.data.get("password2")
        if password != password2:
            return Response({"message": "两次密码输入不一致， 请重新输入"}, status=status.HTTP_304_NOT_MODIFIED)
        # 将密码关联到用户
        user = User.objects.get(id=user_id)
        user.set_password(password)  # 对密码进行为密码
        user.save()

        # 手动生成token

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 加载生成载荷函数
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 加载生成token函数

        payload = jwt_payload_handler(user)  # 生成载荷
        token = jwt_encode_handler(payload)  # 根据载荷生成token

        return Response({"message": "OK"}, status=status.HTTP_202_ACCEPTED)


class VerifyIdentificationView(APIView):
    # GET / accounts / 13827451655 / password / token /?sms_code = 838604
    # 查询参数的方式
    def get(self, request, mobile):
        """验证用户身份"""
        # 1. 获得请求的参数：mobile， 短信验证码, 当前要修改密码的用户
        user = User.objects.get(mobile=mobile)
        sms_code = request.query_params.get('sms_code')
        # 2  验证参数的正确性
        redis_conn = get_redis_connection('verify_code')
        try:
            real_sms_code = redis_conn.get('sms_%s' % mobile)
        except Exception as e:
            logger.error(e)
            return Response({"message": "数据库链接异常"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if real_sms_code:
            if sms_code != real_sms_code.decode():
                return Response({"message": "验证码错误"}, status=status.HTTP_304_NOT_MODIFIED)
            else:
                return Response({'user_id': user.id, 'access_token': mobile})


class SMSCodeView(APIView):
    """发送短信验证码"""

    # GET http: // api.meiduo.site: 8000 / sms_codes /?access_token = undefined
    def get(self, request):
        # 0.创建redis连接对象
        mobile = request.query_params.get('access_token')
        redis_conn = get_redis_connection('verify_code')
        # 1.获取此手机号是否有发送过的标记
        flag = redis_conn.get('send_flag_%s' % mobile)
        # 2.如果已发送就提前响应,不执行后续代码
        if flag:  # 如果if成立说明此手机号60秒内发过短信
            return Response({'message': '频繁发送短信'}, status=status.HTTP_400_BAD_REQUEST)

        # 3.生成短信验证码
        sms_code = '%06d' % randint(0, 999999)
        # print(sms_code)
        logger.info(sms_code)
        # 创建redis管道对象
        pl = redis_conn.pipeline()

        # 4.把验证码存储到redis中
        # redis_conn.setex(key, 过期时间, value)
        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 4.1 存储此手机号已发送短信标记
        # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 执行管道
        pl.execute()

        # 5.利用容联云通讯发短信
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)
        # 触发异步任务(让发短信不要阻塞主线程)
        # send_sms_code(mobile, sms_code)
        send_sms_code.delay(mobile, sms_code, constants.SMS_CODE_REDIS_EXPIRES)
        # 6.响应
        return Response(data={'message': "ok"})


class InputAccountView(APIView):

    def get(self, request, username):
        """输入账户名和图片验证码到下一步的表单提交"""
        # 1  根据username 到 mysql 数据库中查询 用户是否存在
        user = User.objects.get(username=username)
        if not user:
            return Response({"message": "用户不存在， 请重新输入"})

        # 1. 获取请求参数
        image_code_id = request.query_params.get("image_code_id")
        image_code = request.query_params.get("text")
        # print(image_code_id)
        # 2. 根据image_code_id 到redis数据库中获取图片验证码
        redis_conn = get_redis_connection("image_codes")
        real_image_code = redis_conn.get('ImageCode_' + image_code_id)
        # print(real_image_code)
        if image_code.lower() != real_image_code.decode().lower():
            # print('错误')
            return Response({'message': '图片验证码错误'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'username': username, "access_token": user.mobile, 'mobile': user.mobile})


class ImageCodeView(APIView):
    # 记得要开redis数据库 redis-server
    # get请求， 路由：
    # 如：GET http://api.meiduo.site:8000/image_codes/e2b35ce0-fb29-46de-b64c-ce28ab90054f/
    def get(self, request, image_code_id):
        """
        获取图片验证码
        :return:
        """
        # 1. 获取到当前的图片编号id
        # image_code_id = request.GET.get('image_code_id')
        # 2. 生成验证码
        name, text, image = captcha.generate_captcha()
        # print('captcha之后', text)
        try:
            # 保存当前生成的图片验证码内容
            redis_coon = get_redis_connection('image_codes')
            redis_coon.setex('ImageCode_' + image_code_id, 300, text)
        except Exception as error:
            logger.info(error)
            return Response({'errmsg': '保存图片验证码失败'}, status=status.HTTP_400_BAD_REQUEST)

        # 返回响应内容
        resp = HttpResponse(image)
        # 设置内容类型
        resp.content_type = 'image/jpg'
        return resp


class AddressViewSet(CreateModelMixin, UpdateModelMixin, GenericViewSet):
    """地址管理视图集"""
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserAddressSerializer

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    # GET /addresses/ 地址查询
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        user = self.request.user
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,
        })

    # POST /addresses/ 地址新增
    def create(self, request, *args, **kwargs):
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({"message": "地址数量已达上限,请删除后再添加"}, status=status.HTTP_400_BAD_REQUEST)

        return super(AddressViewSet, self).create(request, *args, **kwargs)

    # delete /addresses/<pk>/ 地址删除
    def destroy(self, request, *args, **kwargs):
        address = self.get_object()

        # 逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # put /addresses/pk/status/ 设置默认地址
    @action(methods=["put"], detail=True)
    def status(self, request, pk=None):
        address = self.get_object()

        user = request.user
        user.default_address = address
        user.save()

        return Response({"message": "OK"}, status=status.HTTP_200_OK)

    # put /addresses/pk/title/
    # 需要请求体参数 title
    @action(methods=["put"], detail=True)
    def title(self, request, pk=None):
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(serializer.validated_data)


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
    # 指定认证类
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# url(r'^emails/verification/$', views.EmailView.as_view())
class VerifyEmailView(APIView):
    """激活邮箱"""

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


# url(r'^browse_histories/$', views.UserBrowsingHistoryView.as_view()),
class UserBrowsingHistoryView(CreateAPIView):
    """添加商品浏览记录"""

    # 执行序列化器类
    serializer_class = AddUserBrowsingHistorySerializer
    # 指定需要通过用户登录校验
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取浏览记录"""

        # 1.获取用户id
        user_id = request.user.id
        # 2.建立redis连接
        redis_conn = get_redis_connection('history')
        # 3.获取sku_id列表
        history = redis_conn.lrange('history_%s' % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT - 1)
        # 4.通过sku_id列表获取到所有对应的sku对象,放入列表中
        skus = []
        for sku_id in history:
            sku = SKU.objects.get(id=sku_id)
            skus.append(sku)
        # 5.序列化列表
        skus_dict = SKUSerializer(skus, many=True)
        # 6.返回序列化后的数据
        return Response(skus_dict.data)


class UserAuthorizeView(ObtainJSONWebToken):
    """
    用户认证
    """

    def post(self, request, *args, **kwargs):
        # 调用父类的方法，获取drf jwt扩展默认的认证用户处理结果
        response = super().post(request, *args, **kwargs)

        # 仿照drf jwt扩展对于用户登录的认证方式，判断用户是否认证登录成功
        # 如果用户登录认证成功，则合并购物车
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            response = merge_cart_cookie_to_redis(request, user, response)

        return response
