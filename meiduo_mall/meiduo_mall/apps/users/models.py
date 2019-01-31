from django.db import models
from django.contrib.auth.models import AbstractUser
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSerializer, BadData
from django.conf import settings

from meiduo_mall.utils.models import BaseModel
from . import constants


class User(AbstractUser):
    """自定义用户模型类"""
    # 添加额外的手机号码字段
    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号码")
    # 添加邮箱是否验证
    email_active = models.BooleanField(verbose_name="邮箱验证状态", default=False)
    # 默认地址
    default_address = models.ForeignKey("Address", on_delete=models.SET_NULL, related_name="users",
                                        blank=True, null=True, verbose_name="默认地址")

    class Meta:
        db_table = 'tb_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def generate_verify_email_url(self):
        """生成邮箱验证的链接"""
        # 获取加密类对象
        serializer = TJWSerializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
        # 构造需加密的数据
        data = {"user_id": self.id, "email": self.email}
        # 加密数据并赋值保存
        token = serializer.dumps(data).decode()
        # 拼接链接
        verfity_url = 'http://www.meiduo.site:8080/success_verify_email.html?token=' + token
        # 返回链接
        return verfity_url

    @staticmethod
    def check_email(token):
        """验证邮箱"""

        serializer = TJWSerializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
        # 验证邮箱数据
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        user_id = data.get('user_id')
        email = data.get('email')
        try:
            user = User.objects.get(id=user_id, email=email)
        except User.DoesNotExist:
            return None
        else:
            return user


class Address(BaseModel):
    """地址模型类"""

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name="addresses", verbose_name="用户")
    title = models.CharField(verbose_name="地址名称", max_length=20)
    receiver = models.CharField(verbose_name="收货人名称", max_length=20)
    province = models.ForeignKey("areas.Area", on_delete=models.PROTECT,
                                 related_name="province_addresses", verbose_name="省")
    city = models.ForeignKey("areas.Area", on_delete=models.PROTECT,
                             related_name="city_addresses", verbose_name="市")
    district = models.ForeignKey("areas.Area", on_delete=models.PROTECT, related_name="district_addresses",
                                 verbose_name="区")
    place = models.CharField(verbose_name="地址", max_length=50)
    mobile = models.CharField(verbose_name="手机", max_length=11)
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')
    class Meta:
        db_table = "tb_address"
        verbose_name = "地址"
        verbose_name_plural = verbose_name
        ordering = ["-update_time"]
