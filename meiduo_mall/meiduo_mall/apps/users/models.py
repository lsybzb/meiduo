from django.db import models
from django.contrib.auth.models import AbstractUser
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSerializer, BadData
from django.conf import settings
from . import constants

# Create your models here.

class User(AbstractUser):
    """
    自定义用户模型类
    继承Django默认的用户类型,添加所需字段
    """
    # 添加额外的手机号码字段
    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号码")
    # 添加邮箱是否验证
    email_active = models.BooleanField(verbose_name="邮箱验证状态", default=False)

    class Meta:
        db_table = 'tb_user'
        verbose_name = '用户'
        # 站点中的复数形式任然显示'用户',不加s
        verbose_name_plural = verbose_name


    def generate_verify_email_url(self):
        """生成邮箱验证的链接"""
        # 获取加密类对象
        # 构造需加密的数据
        # 加密数据并赋值保存
        # 拼接链接
        # 返回链接
        serializer = TJWSerializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
        data = {"user_id": self.id, "email": self.email}
        token = serializer.dumps(data).decode()
        verfity_url = 'http://www.meiduo.site:8080/success_verify_email.html?token=' + token
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