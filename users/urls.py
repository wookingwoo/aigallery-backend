from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, RegisterView, FriendshipViewSet, FriendRequestViewSet, DecoratedTokenObtainPairView, DecoratedTokenRefreshView

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')
router.register(r'friendships', FriendshipViewSet, basename='friendship')
router.register(r'friend-requests', FriendRequestViewSet, basename='friend-request')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', DecoratedTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', DecoratedTokenRefreshView.as_view(), name='token_refresh'),
] 