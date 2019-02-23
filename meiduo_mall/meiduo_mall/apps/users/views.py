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

from carts.utils import merge_cart_cookie_to_redis
from goods.models import SKU
from goods.serializers import SKUSerializer
from users import constants
from users.models import User
from users.serializers import AddUserBrowsingHistorySerializer
from . import serializers


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
        history = redis_conn.lrange('history_%s' % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT-1)
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
