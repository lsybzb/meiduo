from django.db import models

# Create your models here.

class Area(models.Model):
    """省市区模型类"""
    name = models.CharField(verbose_name="名称", max_length=20)
    parent = models.ForeignKey('self',                      # 关联外键的字段指向自身
                               on_delete=models.SET_NULL,   # 主键删除时,设置为空
                               related_name='subs',         # 设置下级查询的方式
                               null=True,                  # 设置允许为空白
                               verbose_name="行政区划")      # 站点中显示的名称
    class Meta:
        db_table = "tb_areas"
        verbose_name = "行政区划"
        verbose_name_plural = "行政区划"

    # 定义显示查询输出显示方式
    def __str__(self):
        return self.name