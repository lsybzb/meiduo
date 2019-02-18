from rest_framework import serializers
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