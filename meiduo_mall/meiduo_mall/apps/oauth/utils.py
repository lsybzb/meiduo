from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData

from . import constants


def generate_save_user_token(openid):
    """
    生成保存用户数据的token
    :param openid: 用户的openid
    :return: token
    """
    # 创建加密类的实例对象
    serializer = Serializer(settings.SECRET_KEY, expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)
    # 构造字典
    data = {'openid': openid}
    # 加密返回字节流,解码
    token = serializer.dumps(data).decode()

    return token


def check_save_user_token(access_token):
    # 创建加密类的实例对象

    serializer = Serializer(settings.SECRET_KEY, expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)

    try:
         data = serializer.loads(access_token)
    except BadData:
        return None
    else:
        return data.get('openid')
