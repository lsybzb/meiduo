from rest_framework import serializers

# from meiduo_mall.meiduo_mall.apps.oauth.models import OAuthQQUser, SinaAuthUser
# from meiduo_mall.meiduo_mall.apps.users.models import User
from oauth.models import OAuthQQUser, SinaAuthUser
from users.models import User
from .utils import check_save_user_token
from itsdangerous import BadData
from rest_framework.response import Response
from rest_framework import status
from django_redis import get_redis_connection

class QQAuthUserSerializer(serializers.Serializer):
    """qq登陆创建用户的序列化器类"""

    # 1.定义序列化字段
    mobile = serializers.CharField(label="手机号码", max_length=11)
    password = serializers.CharField(label="密码", min_length=8, max_length=20, write_only=True)
    sms_code = serializers.CharField(label="短信验证码")
    access_token = serializers.CharField(label="QQopenid", write_only=True)

    def validate(self, attrs):
    # 2.提取access_token,解密,并放入校验字典中
        access_token = attrs.get('access_token')

        try:
            openid = check_save_user_token(access_token)
        except BadData:
            raise serializers.ValidationError("无效的access_token")

        attrs['openid'] = openid

    # 3.校验短信验证码
        mobile = attrs.get('mobile')
        sms_code = attrs.get('sms_code')
        redis_conn = get_redis_connection('verify_code')
        real_sms_code = redis_conn.get('sms_code_%s' % mobile).decode()
        if real_sms_code != sms_code:
            raise serializers.ValidationError("短信验证码错误")

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            pass
        else:
        # 4.如果用户存在,检查密码
            if not user.check_password(attrs.get('password')):
                raise serializers.ValidationError("密码错误")
            # 密码正确,将获取到的用户对象放入校验字典
            attrs['user'] = user
            # 密码错误,抛出错误
        return attrs

    def create(self, validated_data):


        # 5.用户不存在
        user = validated_data.get('user')

        self.context['view'].user = user

        if not user:
            # 6.创建用户,通过创建类对象的方式,只需对数据库进行1次写入
            user = User(
                username=validated_data.get('mobile'),
                mobile=validated_data.get('mobile')
            )
            user.set_password(validated_data.get('password'))
            user.save()
        # 7.用户存在,绑定openid
        OAuthQQUser.objects.create(
            user=user,
            openid=validated_data.get('openid')
        )
        # 8.返回user对象
        return user


class SinaAuthUserSerializer(serializers.Serializer):
    """ 绑定用户的序列化器"""

    access_token = serializers.CharField(label='操作凭证')
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    password = serializers.CharField(label='密码', max_length=20)
    sms_code = serializers.CharField(label='短信验证码')

    def validate(self, attrs):
        # 验证短信验证码
        redis_conn = get_redis_connection('verify_code')
        # 获取当前用户手机号码
        mobile = attrs.get('mobile')
        real_sms_code = redis_conn.get('sms_code_%s' % mobile)
        # 获取前端传来的验证码
        sms_code = attrs.get('sms_code')
        if real_sms_code.decode() != sms_code:  # 从redis中取出的验证码为bytes
            raise serializers.ValidationError('验证码错误')

        user = None
        try:
            # 判断手机号码是否为新用户
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 如果出现异常说明是新用户
            pass
        else:
            # 无异常表明此手机号为已注册用户
            if not user.check_password(attrs.get('password')):
                raise serializers.ValidationError('已存在用户,但密码不正确')
            else:
                attrs['user'] = user
        return attrs

    def create(self, validated_data):
        """绑定user与openid"""
        user = validated_data.get('user')
        # 如果用户不存在,就新增一个用户
        if not user:
            user = User(
                username=validated_data.get('mobile'),
                password=validated_data.get('password'),
                mobile=validated_data.get('mobile')
            )
            # 对密码进行加密
            user.set_password(validated_data.get('password'))
            user.save()

        # 绑定user与access_token
        SinaAuthUser.objects.create(
            user=user,
            access_token=validated_data.get('access_token')
        )

        return user
