from rest_framework import serializers

from orders.models import OrderInfo, OrderGoods
from . import models


# class ChannelSerializer(serializers.ModelSerializer):
#     pass
#
# class CategorySerializer(serializers.ModelSerializer):
#     pass

class SKUSerializer(serializers.ModelSerializer):
    """商品列表界面序列化器"""

    class Meta:
        model = models.SKU
        fields = ['id', 'name', 'price', 'default_image_url', 'comments']


class OrderSKUSerializer(serializers.ModelSerializer):
    """商品序列化器"""

    class Meta:
        model = models.SKU
        fields = ['id', 'default_image_url', 'name']


class OrderGoodsSerializer(serializers.ModelSerializer):
    """订单spu序列化器"""

    sku = OrderSKUSerializer()

    class Meta:
        model = OrderGoods
        fields = ['id', 'order_id', 'sku_id', 'sku', 'price', 'count']


class OrdersInfoSerializer(serializers.ModelSerializer):
    """订单信息序列化器"""

    skus = OrderGoodsSerializer(many=True)
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = OrderInfo
        fields = ['create_time', 'order_id', 'total_count',
                  'total_amount', 'freight', 'pay_method',
                  'status', 'skus']
