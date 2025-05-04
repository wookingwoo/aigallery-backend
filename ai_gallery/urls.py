"""
URL configuration for ai_gallery project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="AI Gallery API",
        default_version="v1",
        description="""
# AI Gallery API 문서

AI Gallery는 사용자가 이미지를 업로드하고 AI를 활용하여 다양한 효과를 적용할 수 있는 소셜 미디어 플랫폼입니다.

## 주요 기능

### 사용자 관리
- 회원가입 및 로그인
- 프로필 관리
- JWT 인증

### 갤러리
- 이미지 업로드 및 공유
- 이미지 검색 및 필터링
- 좋아요 및 댓글

### AI 이미지 변환
- 원본 이미지를 만화 스타일로 변환
- 다양한 AI 모델 선택 가능
- 사용자 프롬프트를 통한 세부 설정

## 인증
API 요청시 다음 헤더를 포함해야 합니다:
```
Authorization: Bearer {access_token}
```

## 파일 업로드
이미지 업로드는 `multipart/form-data` 형식을 사용합니다.
        """,
        terms_of_service="https://wookingwoo.com",
        contact=openapi.Contact(email="contact@wookingwoo.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/gallery/", include("gallery.urls")),
    path("api/ai/", include("ai_image_converter.urls")),
    # Swagger documentation
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

# Add static and media URLs in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
