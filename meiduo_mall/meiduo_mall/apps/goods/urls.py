from django.conf.urls import url

from . import views


urlpatterns = [
    # 商品列表界面
    url(r'^categories/(?P<category_id>\d+)/skus/$', views.SKUListView.as_view()),
    url(r'^orderslist/$', views.OderList.as_view()),    # 订单列表
    url(r'^skus/(?P<sku_id>\d+)/comments/$', views.SKUCommentView.as_view()), # 商品评论展示
]