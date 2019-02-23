from rest_framework import serializers

from goods.models import SKU
from orders.models import OrderInfo


class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')

    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url', 'price', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)


class SaveOrderSerializer(serializers.ModelSerializer):
    """
    下单数据序列化器
    """
    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method')
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True,
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        pass
        # 获取当前下单用户

        # 生成订单编号

        # 保存订单基本信息数据 OrderInfo

        # 从redis中获取购物车结算商品数据

        # 遍历结算商品：

        # 判断商品库存是否充足

        # 减少商品库存，增加商品销量

        # 保存订单商品数据

        # 在redis购物车中删除已计算商品数据