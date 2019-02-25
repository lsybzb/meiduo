from django.conf.urls import url

from orders import views

urlpatterns = [
    url(r'^orders/$', views.SaveOrderView.as_view()),   # 订单保存
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view()),  # 订单结算
    url(r'^orders/(?P<order_id>\d+)/uncommentgoods/$', views.CommentListView.as_view()), # 订单评论界面展示
]