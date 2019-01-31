from django.conf.urls import url
from rest_framework import routers
from rest_framework_jwt.views import obtain_jwt_token

from . import views

urlpatterns = [
    # 用户名数量查询,看是否已经注册
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
    # 手机号数量查询
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    # 新建用户
    url(r'^users/$', views.CreateUserView.as_view()),
    # 自动签发jwt令牌路由
    url(r'^authorizations/$', obtain_jwt_token),
    # 用户个人中心
    url(r'^user/$', views.UserDetailView.as_view()),
    # 发送邮件视图
    url(r'^email/$', views.EmailView.as_view()),
    # 验证邮件视图
    url(r'^emails/verification/$', views.VerifyEmailView.as_view()),
]

router = routers.DefaultRouter()
router.register(r'addresses', views.AddressViewSet, base_name="addresses")
urlpatterns += router.urls