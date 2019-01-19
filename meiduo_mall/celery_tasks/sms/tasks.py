import logging
from celery_tasks.main import app
from .yuntongxun.sms import CCP

logger = logging.getLogger('django')

# 验证码短信模板
SMS_CODE_TEMP_ID = 1

def send_sms_code(mobile, code, expires):
    try:
        ccp = CCP()
        result = ccp.send_template_sms(mobile, [code, expires], SMS_CODE_TEMP_ID)
    except Exception as e:
        logger.error("发送验证码短信[异常][ mobile: %s, message: %s ]" % (mobile, e))
    else:
        if result == 0:
            logger.info("发送验证码短信[正常][ mobile: %s ]" % mobile)
        else:
            logger.warning("发送验证码短信[失败][ mobile: %s ]" % mobile)