# from datetime import timezone
# from time import timezone
from django.utils import timezone
from rest_framework import serializers
from decimal import Decimal
from django_redis import get_redis_connection
from django.db import transaction

from goods.models import SKU
from goods.serializers import OrderSKUSerializer
from meiduo_mall.utils.exceptions import logger
from .models import OrderInfo, OrderGoods


# class OrderSKUSerializer(serializers.ModelSerializer):
#     """商品序列化器"""
#
#     class Meta:
#         model = SKU
#         fields = ['id', 'default_image_url', 'name']


class SaveCommentSerializer(serializers.ModelSerializer):
    """保存评论序列化器

    传入数据
    order:			order_id	order_info & ordergoods
    sku:			sku_id		ordergoods
    comment: 		评论			ordergoods
    score: 			评分			ordergoods
    is_anonymous:	是否匿名		ordergoods

    需修改数据
    is_commented
    """

    class Meta:
        model = OrderGoods
        fields = ['order_id', 'sku_id', 'comment', 'score',
                  'is_anonymous', 'is_commented']

    def validate(self, data):
        """
        1.序列化器校验数据返回
        :param data:
        :return:
        """

        comment = data.get('comment')
        score = data.get('score')
        is_anonymous = data.get('is_anonymous', False)
        print("comment", comment)
        print("score", score)
        print("is_anonymous", is_anonymous)
        if not all([comment, score]):
            raise serializers.ValidationError("参数不全")
        return data

    def update(self, instance, validated_data):
        """
        1.保存ordergoods信息,修改评论状态
        2.通过该订单id查询计算一共有多少个商品
        3.过滤查询并统计该订单下已经评价的id有多少个
        4.判断2与3两个数据是否相同,
		相同则修改order_info的订单状态
        :param validated_data:
        :return:
        """

        instance.comment = validated_data.get('comment')
        instance.score = validated_data.get('score')
        instance.is_anonymous = validated_data.get('is_anonymous')
        instance.is_commented = True
        instance.save()


        order_id = instance.order_id
        total_count = OrderGoods.objects.filter(order_id=order_id).count()
        print("total_count", total_count)
        commented_count = OrderGoods.objects.filter(order_id=order_id, is_commented=True).count()
        print("commented_count", commented_count)

        if (total_count !=0) and (total_count == commented_count):
            try:
                order_info = OrderInfo.objects.get(order_id=order_id)
                order_info.status = 5
                order_info.save()
            except Exception:
                raise serializers.ValidationError("修改订单状态并保存到数据库时失败")
        return instance



class CommentGoodsSerializer(serializers.ModelSerializer):
    """订单spu序列化器"""

    sku = OrderSKUSerializer()

    class Meta:
        model = OrderGoods
        fields = ['id', 'order_id', 'sku_id', 'sku', 'price']


class SaveOrderSerializer(serializers.ModelSerializer):
    """保存订单序列化器"""

    class Meta:
        model = OrderInfo
        fields = ['order_id', 'pay_method', 'address']
        # order_id 只做输出, pay_method/address只做输入
        read_only_fields = ['order_id']
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
        """
        保存订单
        """
        # 获取当前下单用户
        user = self.context['request'].user

        # 组织订单编号 20170903153611+user.id
        # timezone.now() -> datetime
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

        address = validated_data['address']
        pay_method = validated_data['pay_method']

        # 生成订单
        with transaction.atomic():
            # 创建一个保存点
            save_id = transaction.savepoint()

            try:
                # 创建订单信息
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal(0),
                    freight=Decimal(10),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
                        'CASH'] else OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                )
                # 获取购物车信息
                redis_conn = get_redis_connection("cart")
                redis_cart = redis_conn.hgetall("cart_%s" % user.id)
                cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)

                # 将bytes类型转换为int类型
                cart = {}
                for sku_id in cart_selected:
                    cart[int(sku_id)] = int(redis_cart[sku_id])

                # # 一次查询出所有商品数据
                # skus = SKU.objects.filter(id__in=cart.keys())

                # 处理订单商品
                sku_id_list = cart.keys()
                for sku_id in sku_id_list:
                    while True:
                        sku = SKU.objects.get(id=sku_id)

                        sku_count = cart[sku.id]

                        # 判断库存
                        origin_stock = sku.stock  # 原始库存
                        origin_sales = sku.sales  # 原始销量

                        if sku_count > origin_stock:
                            transaction.savepoint_rollback(save_id)
                            raise serializers.ValidationError('商品库存不足')

                        # 用于演示并发下单
                        # import time
                        # time.sleep(5)

                        # 减少库存
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()
                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count

                        # 根据原始库存条件更新，返回更新的条目数，乐观锁
                        ret = SKU.objects.filter(id=sku.id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                        if ret == 0:
                            continue

                        # 累计商品的SPU 销量信息
                        sku.goods.sales += sku_count
                        sku.goods.save()

                        # 累计订单基本信息的数据
                        order.total_count += sku_count  # 累计总金额
                        order.total_amount += (sku.price * sku_count)  # 累计总额

                        # 保存订单商品
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price,
                        )

                        # 更新成功
                        break

                # 更新订单的金额数量信息
                order.total_amount += order.freight
                order.save()

            except serializers.ValidationError:
                raise
            except Exception as e:
                logger.error(e)
                transaction.savepoint_rollback(save_id)
                raise

            # 提交事务
            transaction.savepoint_commit(save_id)

            # 更新redis中保存的购物车数据
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, *cart_selected)
            pl.srem('cart_selected_%s' % user.id, *cart_selected)
            pl.execute()
            return order


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
    # float 1.23 ==> 123 * 10 ^ -2  --> 1.299999999
    # Decimal  1.23    1    23
    # max_digits 一共多少位；decimal_places：小数点保留几位
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)
