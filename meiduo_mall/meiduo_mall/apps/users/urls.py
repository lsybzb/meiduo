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
    # 登陆验证
    # url(r'^authorizations/$', obtain_jwt_token),
    url(r'^authorizations/$', views.UserAuthorizeView.as_view()),
    # 用户个人中心
    url(r'^user/$', views.UserDetailView.as_view()),
    # 发送邮件视图
    url(r'^email/$', views.EmailView.as_view()),
    # 验证邮件视图
    url(r'^emails/verification/$', views.VerifyEmailView.as_view()),
    url(r'^browse_histories/$', views.UserBrowsingHistoryView.as_view()),


    # 图片验证码
    url(r'^image_codes/(?P<image_code_id>[\w-]+)/$', views.ImageCodeView.as_view()),

    # 输入账户名
    url(r'^accounts/(?P<username>\w{5,20})/sms/token/', views.InputAccountView.as_view()),

    # 获取短信验证码
    url(r'^sms_codes/', views.SMSCodeView.as_view()),

    # 验证用户身份
    url(r'^accounts/(?P<mobile>\w{5,20})/password/token/', views.VerifyIdentificationView.as_view()),

    # 修改密码
    url(r"^users/(?P<user_id>\d.*)/password/$", views.ResetPasswordView.as_view()),

    # 重置密码
    url(r'^users/\d+/password/$', views.ResetPasswords.as_view()),

]

router = routers.DefaultRouter()
router.register(r'addresses', views.AddressViewSet, base_name="addresses")
urlpatterns += router.urls
