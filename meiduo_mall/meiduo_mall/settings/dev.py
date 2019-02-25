""" 开发环境配置
Django settings for meiduo_mall project.

Generated by 'django-admin startproject' using Django 1.11.11.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import sys
import datetime

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
# /meiduo/meiduo_mall/meiduo_mall
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 为apps中的子应用添加导包路径
sys.path.insert(0,os.path.join(BASE_DIR, 'apps'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'crjyg*wri(ck5^3+!*etzxpov9fhtfwv9+#h6zcmi07y$jph75'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'www.meiduo.site', 'api.meiduo.site', '192.168.40.131']


# Application definition

INSTALLED_APPS = [
    # ----------自带----------
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # ----------第三方应用----------
    'rest_framework', # DRF模块
    'corsheaders',  #
    'ckeditor', # 富文本编辑器
    'ckeditor_uploader', # 富文本编辑器上传图片模块
    'django_crontab', # 定时生成首页任务

    # ----------自建应用----------
    # 用户模型应用
    'users.apps.UsersConfig',
    # QQ登陆子应用
    'oauth.apps.OauthConfig',
    # 短信验证码发送子应用
    'verifications.apps.VerificationsConfig',
    # 收货地址子应用
    'areas.apps.AreasConfig',
    # 商品子应用
    'goods.apps.GoodsConfig',
    # 广告子应用
    'contents.apps.ContentsConfig',
    # 购物车
    'carts.apps.CartsConfig',
    # 订单
    'orders.apps.OrdersConfig',
    # 支付宝支付
    'payment.apps.PaymentConfig',
]

# 重新指定用户模型类
AUTH_USER_MODEL = 'users.User'


MIDDLEWARE = [
    # 添加跨域请求中间件
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
# 指定总路由
ROOT_URLCONF = 'meiduo_mall.urls'
# 指定模板文件夹
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# 生成的静态html文件保存目录
GENERATED_STATIC_HTML_FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'front_end_pc')

WSGI_APPLICATION = 'meiduo_mall.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
# 配置mysql服务器
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '192.168.40.131',  # 数据库主机(虚拟机,固定ip)
        'PORT': 3306,  # 数据库端口
        'USER': 'meiduo',  # 数据库用户名
        'PASSWORD': 'meiduo',  # 数据库用户密码
        'NAME': 'meiduo_mall'  # 数据库名字
    }
}
# 配置redis服务器
CACHES = {
    "default": {   # 指定默认的信息存储位置
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.40.131:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "session": {   # 指定session存储位置与名称
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.40.131:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "verify_code": {  # 指定存储短信码的位置与名称
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.40.131:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "history": {   # 用户浏览记录
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.40.131:6379/3",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "cart": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.40.131:6379/4",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "image_codes": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.40.131:6379/4",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "session"

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/
# 设置本地化语言为中文
# LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'zh-hans'

# TIME_ZONE = 'UTC'
# 设置本地时区为上海,同北京时区
TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
# 添加日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # 是否禁用已经存在的日志器
    'formatters': {  # 日志信息显示的格式
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(lineno)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(module)s %(lineno)d %(message)s'
        },
    },
    'filters': {  # 对日志进行过滤
        'require_debug_true': {  # django在debug模式下才输出日志
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {  # 日志处理方法
        'console': {  # 向终端中输出日志
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {  # 向文件中输出日志
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(os.path.dirname(BASE_DIR), "logs/meiduo.log"),  # 日志文件的位置
            'maxBytes': 300 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose'
        },
    },
    'loggers': {  # 日志器
        'django': {  # 定义了一个名为django的日志器
            'handlers': ['console', 'file'],  # 可以同时向终端与文件中输出日志
            'propagate': True,  # 是否继续传递日志信息
            'level': 'INFO',  # 日志器接收的最低日志级别
        },
    }
}
# REST framework配置信息
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'meiduo_mall.utils.exceptions.exception_handler', # 指定自定义处理函数,加入MySQL与Redis
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'meiduo_mall.utils.pagination.StandardResultsSetPagination',
}

# 跨域请求白名单
CORS_ORIGIN_WHITELIST = (
    '127.0.0.1:8080',
    'localhost:8080',
    'www.meiduo.site:8080', # 前端域名别名
    'api.meiduo.site:8000', # 后端位置
)
CORS_ALLOW_CREDENTIALS = True  # 允许携带cookie

# JWT 设置
JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=1),   # 设置jwt过期时间
    "JWT_RESPONSE_PAYLOAD_HANDLER": 'users.utils.jwt_response_payload_handler', # 指定自定义jwt处理函数
}


AUTHENTICATION_BACKENDS = [
    'users.utils.UsernameMobileAuthBackend',
]

# 配置qq登陆应用的id信息
QQ_CLIENT_ID = '101474184'
QQ_CLIENT_SECRET = 'c6ce949e04e12ecc909ae6a8b09b637c'
QQ_REDIRECT_URI = 'http://www.meiduo.site:8080/oauth_callback.html'

# 配置邮件发送客户端
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.163.com'
EMAIL_PORT = 25
#发送邮件的邮箱
EMAIL_HOST_USER = 'wwww164@163.com'
#在邮箱中设置的客户端授权密码
EMAIL_HOST_PASSWORD = 'test12345678'
#收件人看到的发件人
EMAIL_FROM = 'python<wwww164@163.com>'

# DRF扩展
REST_FRAMEWORK_EXTENSIONS = {
    # 缓存时间
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 60,
    # 缓存存储
    'DEFAULT_USE_CACHE': 'default',
}

# django文件存储
DEFAULT_FILE_STORAGE = "meiduo_mall.utils.fastdfs.fdfs_storage.FastDFSStorage"

# FastDFS
FDFS_URL = 'http://image.meiduo.site:8888/'
FDFS_CLIENT_CONF = os.path.join(BASE_DIR, 'utils/fastdfs/client.conf')

# 富文本编辑器ckeditor配置
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',  # 工具条功能
        'height': 300,  # 编辑器高度
        # 'width': 300,  # 编辑器宽
    },
}
CKEDITOR_UPLOAD_PATH = ''  # 上传图片保存路径，使用了FastDFS，所以此处设为''

# 定时任务配置
CRONJOBS = [
    # 5分钟执行一次静态主页文件
    ('*/1 * * * *', 'contents.crons.generate_static_index_html', '>> /Users/lisi/Course/code/bk_course/python_08_mdproject/meiduo/meiduo_mall/logs/crontab.log')
]

# 解决crontab中文问题
CRONTAB_COMMAND_PREFIX = 'LANG_ALL=zh_cn.UTF-8'

ALIPAY_APPID = "2016092200574009"
ALIPAY_URL = "https://openapi.alipaydev.com/gateway.do"
ALIPAY_DEBUG = True