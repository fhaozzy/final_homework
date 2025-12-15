from rest_framework.routers import DefaultRouter

from accounts.views import RoleViewSet, UserRoleViewSet, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"roles", RoleViewSet, basename="role")
router.register(r"user-roles", UserRoleViewSet, basename="user-role")

urlpatterns = router.urls

