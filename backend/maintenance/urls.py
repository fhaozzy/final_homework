from rest_framework.routers import DefaultRouter

from maintenance.views import MaintenanceViewSet

router = DefaultRouter()
router.register(r"maintenance", MaintenanceViewSet, basename="maintenance")

urlpatterns = router.urls

