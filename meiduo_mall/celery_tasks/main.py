from celery import Celery

# 为celery使用django配置文件进行设置
import os
# 如果需要用配置文件时,指定去哪里加载
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'

# 创建celery应用
app = Celery('meiduo')

# 导入celery配置
app.config_from_object('celery_tasks.config')

# 自动注册celery任务
# sms:发送短信
# email:发送验证邮件
app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email'])
