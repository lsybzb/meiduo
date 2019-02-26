from decimal import Decimal
from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework.generics import CreateAPIView, ListAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from goods.models import SKU
from orders.models import OrderGoods
from orders.serializers import OrderSettlementSerializer, SaveOrderSerializer, CommentGoodsSerializer, \
    SaveCommentSerializer


class SaveCommentUpdateView(GenericAPIView):
    """
    保存评论视图
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        print(order_id)
        sku_id = request.data.get('sku')
        ordergoods = OrderGoods.objects.get(order_id=order_id, sku_id=sku_id)
        comment = request.data.get('comment')
        score = request.data.get('score')
        is_anonymous = request.data.get('is_anonymous', False)

        comment_dict = {
            "order_id": order_id,
            "sku_id":sku_id,
            "comment":comment,
            "score":score,
            "is_anonymous":is_anonymous
        }
        serializer = SaveCommentSerializer(instance=ordergoods, data=comment_dict)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message":"ok"})

class CommentListView(ListAPIView):
    """
    商品评价界面展示
    """

    permission_classes = [IsAuthenticated]
    pagination_class = None
    serializer_class = CommentGoodsSerializer

    def get_queryset(self):
        order_id = self.kwargs.get('order_id')
        return OrderGoods.objects.filter(order_id=order_id)

class OrderSettlementView(APIView):
    """
    订单结算
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取
        """
        user = request.user

        # 从购物车中获取用户勾选要结算的商品信息
        redis_conn = get_redis_connection('cart')
        redis_cart = redis_conn.hgetall('cart_%s' % user.id)
        cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)

        cart = {}
        for sku_id in cart_selected:
            cart[int(sku_id)] = int(redis_cart[sku_id])

        # 查询商品信息
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]

        # 运费
        freight = Decimal('10.00')

        serializer = OrderSettlementSerializer({'freight': freight, 'skus': skus})
        return Response(serializer.data)

class SaveOrderView(CreateAPIView):
    """
    保存订单
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SaveOrderSerializer