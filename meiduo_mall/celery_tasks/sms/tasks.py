import logging

from celery_tasks.main import app
from .yuntongxun.sms import CCP

from . import constants

logger = logging.getLogger("django")


@app.task(name='send_sms_code')
def send_sms_code(mobile, code, expires):
    """
    发送短信验证码
    :param mobile: 手机号
    :param code: 验证码
    :param expires: 有效期
    :return: None
    """

    try:
        ccp = CCP()
        result = ccp.send_template_sms(mobile, [code, expires], constants.SMS_CODE_TEMP_ID)
    except Exception as e:
        logger.error("发送验证码[异常][ mobile: %s, message: %s ]" % (mobile, e))
    else:
        if result == 0:
            logger.info("发送验证码[正常][ mobile: %s ]" % mobile)
        else:
            logger.warning("发送验证码[失败][ mobile: %s ]" % mobile)
