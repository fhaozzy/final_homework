from rest_framework.routers import DefaultRouter

from inventory.views import EquipmentCategoryViewSet, EquipmentViewSet

router = DefaultRouter()
router.register(r"equipment-categories", EquipmentCategoryViewSet, basename="equipment-category")
router.register(r"equipment", EquipmentViewSet, basename="equipment")

urlpatterns = router.urls
