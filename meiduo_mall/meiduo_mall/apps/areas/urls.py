from rest_framework.routers import DefaultRouter
from areas import views

urlpatterns = []


# 创建路由器对象
router = DefaultRouter()
# 注册
router.register(r'areas', views.AreasViewSet, base_name="areas")
urlpatterns += router.urls