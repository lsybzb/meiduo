from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class User(AbstractUser):
    """
    自定义用户模型类
    继承Django默认的用户类型,添加所需字段
    """
    # 添加额外的手机号码字段
    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号码")

    class Meta:
        db_table = 'tb_user'
        verbose_name = '用户'
        # 站点中的复数形式任然显示'用户',不加s
        verbose_name_plural = verbose_name
