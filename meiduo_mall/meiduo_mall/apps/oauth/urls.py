from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
    url(r'^qq/user/$', views.QQAuthUserView.as_view()),
    # sina获取扫码url
    url(r'^sina/authorization/$', views.SinaAuthURLView.as_view()),
    # sina扫码后回调处理
    url(r'^sina/user/$', views.WeiboAuthUserView.as_view()),
]
