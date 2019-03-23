from rest_framework import serializers
import re
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings

from goods.models import SKU
from users import constants
from users.models import User, Address
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

    @staticmethod
    def validate_mobile(value):
        """2.验证手机号码格式是否正确"""
        result = re.match(r'^1[3-9]\d{9}$', value)
        if result is None:
            raise serializers.ValidationError("手机格式错误")
        return value

    @staticmethod
    def validate_allow(value):
        """3.验证是否同意协议"""
        if value != 'true':
            raise serializers.ValidationError("请勾选用户协议")
        return value

    def validate(self, attrs):
        """4.验证两次密码是否相同"""

        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("两次密码不一致")

        # 5.判断短信验证码
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
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token

        return user


class AddressTitleSerializer(serializers.ModelSerializer):
    """修改标题序列化器"""

    class Meta:
        model = Address
        fields = ('title',)


class UserAddressSerializer(serializers.ModelSerializer):
    """
    用户地址序列化器
    """
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    @staticmethod
    def validate_mobile(value):
        """
        验证手机号
        """
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def create(self, validated_data):
        """
        保存
        """
        validated_data['user'] = self.context['request'].user
        return super(UserAddressSerializer, self).create(validated_data)


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


class AddUserBrowsingHistorySerializer(serializers.Serializer):
    """添加用户浏览历史记录"""

    sku_id = serializers.IntegerField(label="商品SKU编码", min_value=1)

    def validate_sku_id(self, data):
        """校验sku_id"""

        try:
            SKU.objects.get(id=data)
        except SKU.DoesNotExist:
            raise serializers.ValidationError("该商品不存在")

        return data

    def create(self, validated_data):
        """
        保存sku_id到redis数据库中
        1.获取用户id
        2.获取sku_id
        3.建立redis数据库连接对象
        4.将redis中存在的相同的sku_id全部删除
        5.将记录存入redis中
        6.限制redis中一个用户浏览记录列表最多保存5条记录
        7.执行管道命令
        8.返回validated_data
        """
        user_id = self.context['request'].user.id
        sku_id = validated_data.get('sku_id')
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        pl.lrem('history_%s' % user_id, 0, sku_id)
        pl.lpush('history_%s' % user_id, sku_id)
        pl.ltrim('history_%s' % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT - 1)
        pl.execute()
        return validated_data
