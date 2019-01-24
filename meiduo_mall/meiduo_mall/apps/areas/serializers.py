from rest_framework import serializers
from .models import Area


class AreaSerializer(serializers.ModelSerializer):
    """行政区序列化器"""

    class Meta:
        model = Area
        fields = ('id', 'name')


class SubAreaSerializer(serializers.ModelSerializer):
    """自行政区序列化器"""
    # 建立自定义序列化器字段
    subs = AreaSerializer(many=True, read_only=True)

    class Meta:
        model = Area
        fields = ('id', 'name', 'subs')

