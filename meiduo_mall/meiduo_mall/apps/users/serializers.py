from rest_framework import serializers
import re
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings

from users.models import User
from celery_tasks.email.tasks import send_verify_email


class CreateUserSerializer(serializers.ModelSerializer):
    """
    新建用户序列化器类
    1.传入参数:
    username, password, password2, sms_code, mobile, allow
    2.验证手机格式是否正确
    3.验证是否同意协议
    4.验证两次密码是否相同
    5.判断短信验证码
    6.创建用户模型
    """
    password2 = serializers.CharField(label="确认密码", write_only=True)
    sms_code = serializers.CharField(label="短信验证码", write_only=True)
    allow = serializers.CharField(label="同意协议", write_only=True)
    token = serializers.CharField(label="jwt令牌", read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'password2', 'mobile', 'sms_code', 'allow', 'token']
        # 添加字段序列化限制
        extra_kwargs = {
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'min_length': 8,
                'max_length': 20,
                'write_only': True,
                'error_messages': {
                    'min_length': '填写8-20个字符的密码',
                    'max_length': '填写8-20个字符的密码'
                }
            }
        }

    def validate_mobile(self, value):
        """2.验证手机号码格式是否正确"""
        result = re.match(r'^1[3-9]\d{9}$', value)
        if result is None:
            raise serializers.ValidationError("手机格式错误")
        return value

    def validate_allow(self, value):
        """3.验证是否同意协议"""
        if value != 'true':
            raise serializers.ValidationError("请勾选用户协议")
        return value

    def validate(self, attrs):
        """4.验证两次密码是否相同"""

        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("两次密码不一致")

        """5.判断短信验证码"""
        redis_conn = get_redis_connection('verify_code')

        real_sms_code = redis_conn.get("sms_code_%s" % attrs["mobile"])

        if real_sms_code is None:
            raise serializers.ValidationError("短信验证码过期或无效")

        if attrs['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError("短信验证码不正确")
        return attrs

    def create(self, validated_data):
        """6.创建用户模型"""
        # 删除传入数据中不需要存储到数据库的字段
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        # User.objects.create(**validated_data)

        # 创建用户模型类对象
        user = User(**validated_data)
        # 通过用户模型类方法加密密码
        user.set_password(validated_data['password'])
        # 保存用户对象到数据库
        user.save()

        # 加入jwt认证机制
        JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = JWT_PAYLOAD_HANDLER(user)
        token = jwt_encode_handler(payload)
        user.token = token

        return user


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'email_active')


class EmailSerializer(serializers.ModelSerializer):
    """保存邮箱的序列化器"""

    class Meta:
        model = User
        fields = ('id', 'email')
        extra_kwargs = {
            'email': {
                'required': True
            }
        }

    def update(self, instance, validated_data):
        """保存用户邮箱,通过邮箱发送验证链接至客户邮箱"""
        email = validated_data.get('email')
        instance.email = email
        instance.save()
        # 获取验证链接
        verfity_url = instance.generate_verify_email_url()
        # 通过邮件发送链接
        send_verify_email.delay(email, verfity_url)

        return instance
