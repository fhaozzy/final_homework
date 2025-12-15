from rest_framework.routers import DefaultRouter

from inventory.views import ConsumableViewSet, EquipmentCategoryViewSet, EquipmentViewSet, StockTxnViewSet

router = DefaultRouter()
router.register(r"equipment-categories", EquipmentCategoryViewSet, basename="equipment-category")
router.register(r"equipment", EquipmentViewSet, basename="equipment")
router.register(r"consumables", ConsumableViewSet, basename="consumable")
router.register(r"stock", StockTxnViewSet, basename="stock")

urlpatterns = router.urls
