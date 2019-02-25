from django.db import models
from meiduo_mall.utils.models import BaseModel

# from meiduo_mall.meiduo_mall.apps.users.models import User
from users.models import User


class OAuthQQUser(BaseModel):
    """定义QQ用户模型类"""

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name="用户")
    openid = models.CharField(max_length=64, verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ登录用户数据'
        verbose_name_plural = verbose_name

class SinaAuthUser(BaseModel):
    """新浪登录"""

    user = models.ForeignKey(User, verbose_name='openid关联的用户', on_delete=models.CASCADE)
    access_token = models.CharField(verbose_name='新浪用户唯一标识', db_index=True, max_length=64)

    class Meta:
        db_table = 'tb_oauth_sina'
        verbose_name = 'sina登录用户数据'
        verbose_name_plural = verbose_name