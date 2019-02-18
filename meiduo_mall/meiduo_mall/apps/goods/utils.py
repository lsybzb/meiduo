from collections import OrderedDict

from .models import GoodsChannel


def get_categories():
    """

    :return:
    """

    # categories = {
    #     1: { # 组1
    #         'channels': [{'id':, 'name':, 'url':},{}, {}...],
    #         'sub_cats': [{'id':, 'name':, 'sub_cats':[{},{}]}, {}, {}, ..]
    #     },
    #     2: { # 组2
    #
    #     }
    # }

    # 1.创建一个空白有序字典
    categories = OrderedDict()

    # 2.获取商品频道的查询集,按照组号和组内顺序排序
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')

    # 3.遍历每个频道对象
    for channel in channels:
        # 4.获取频道对象的组号
        group_id = channel.group_id
        # 5.将组号与对应的1级分类及其子类放入字典中
        if group_id not in categories:
            categories[group_id] = {'channels': [], 'sub_cats': []}

        # 获取1级分类的对象
        cat1 = channel.category
        # 6.将1级分类信息放入字典中
        categories[group_id]['channels'].append(
            {
                'id': cat1.id,
                'name': cat1.name,
                'url': channel.url
            }
        )
        # 7.获取1级分类的所有子类对象
        for cat2 in cat1.goodscategory_set.all():
            # 为每个cat2添加属性sub_cats 一个空列表
            cat2.sub_cats = []
            # 获取所有3级分类的对象
            for cat3 in cat2.goodscategory_set.all():
                # 将3级分类添加到2级分类的sub_cats属性列表中
                cat2.sub_cats.append(cat3)  # 直接添加对象,序列化输出后会转为json字典
            categories[group_id]['sub_cats'].append(cat2)

        # 8.返回包含所有分类信息的字典
    return categories
