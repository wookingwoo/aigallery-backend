from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIImageViewSet

router = DefaultRouter()
# HTTP methods GET, POST, DELETE만 지원하는 뷰셋 등록
router.register(r"images", AIImageViewSet, basename="ai-images")

urlpatterns = [
    path("", include(router.urls)),
]
