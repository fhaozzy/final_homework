from rest_framework.routers import DefaultRouter

from borrowing.views import BorrowRequestViewSet

router = DefaultRouter()
router.register(r"borrow/requests", BorrowRequestViewSet, basename="borrow-request")

urlpatterns = router.urls
