from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    RegisterView,
    FriendshipViewSet,
    FriendRequestViewSet,
    DecoratedTokenObtainPairView,
    DecoratedTokenRefreshView,
    CreditInfoView,
    CreditChargeView,
    CreditUsageListView,
    LogoutView,
)

router = DefaultRouter()
router.register(r"accounts", UserViewSet, basename="user")
router.register(r"friendships", FriendshipViewSet, basename="friendship")
router.register(r"friend-requests", FriendRequestViewSet, basename="friend-request")

urlpatterns = [
    path("", include(router.urls)),
    path("register/", RegisterView.as_view(), name="register"),
    path("token/", DecoratedTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", DecoratedTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # 크레딧 관련 URL
    path("credits/", CreditInfoView.as_view(), name="credit-info"),
    path("credits/charge/", CreditChargeView.as_view(), name="credit-charge"),
    path("credits/history/", CreditUsageListView.as_view(), name="credit-history"),
]
