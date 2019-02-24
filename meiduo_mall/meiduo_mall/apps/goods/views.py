from django.shortcuts import render

# Create your views here.
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView, GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import OrderInfo
from .models import SKU, GoodsCategory
from .serializers import SKUSerializer, OrdersInfoSerializer


# class CategoryView(GenericAPIView):
#     """
#     商品列表页面包屑导航
#     """
#     queryset = GoodsCategory.objects.all()
#
#     def get(self, request, pk=None):
#         ret = dict(
#             cat1='',
#             cat2='',
#             cat3=''
#         )
#         category = self.get_object()
#         if category.parent is None:
#             # 当前类别为一级类别
#             ret['cat1'] = ChannelSerializer(category.goodschannel_set.all()[0]).data
#         elif category.goodscategory_set.count() == 0:
#             # 当前类别为三级
#             ret['cat3'] = CategorySerializer(category).data
#             cat2 = category.parent
#             ret['cat2'] = CategorySerializer(cat2).data
#             ret['cat1'] = ChannelSerializer(cat2.parent.goodschannel_set.all()[0]).data
#         else:
#             # 当前类别为二级
#             ret['cat2'] = CategorySerializer(category).data
#             ret['cat1'] = ChannelSerializer(category.parent.goodschannel_set.all()[0]).data
#
#         return Response(ret)

class OrderListPagination(PageNumberPagination):
    page_size = 2  # 每页数量
    page_size_query_param = 'page_size'
    max_page_size = 5

class OderList(ListAPIView):
    """
    1.通过重写GenericAPIView中的get_queryset 通过当前登录的用户获取该用户的订单查询集
    2.通过重写ListModelMixin 的list方法,重新构成字典并加入订单总数量,再返回至前端
    """

    permission_classes = [IsAuthenticated]
    pagination_class = OrderListPagination
    serializer_class = OrdersInfoSerializer

    def get_queryset(self):
        user = self.request.user

        return OrderInfo.objects.filter(user=user).order_by('-create_time')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        count = queryset.count()
        data = {
            "results": serializer.data,
            "count": count
        }
        return Response(data)


class SKUListView(ListAPIView):
    """商品列表界面"""

    # 指定序列化器
    serializer_class = SKUSerializer

    # 指定过滤后端为排序
    filter_backends = [OrderingFilter]

    # 指定排序字段
    ordering_fields = ['create_time', 'price', 'sales']

    # 指定查询集
    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return SKU.objects.filter(is_launched=True, category_id=category_id)
