from django.shortcuts import render
from rest_framework import viewsets, status, parsers, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import CartoonImage
from .serializers import CartoonImageSerializer, CartoonImageCreateSerializer
from .utils import convert_to_cartoon
from django.db.models import Q
import threading
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class CartoonImageViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    API 엔드포인트: 이미지를 만화 스타일로 변환하는 기능

    사용자가 업로드한 이미지를 AI 기반 기술을 사용하여 만화 캐릭터 스타일로 변환합니다.
    변환 과정은 비동기적으로 처리되며, 사용자는 변환 상태를 확인할 수 있습니다.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        """Return images created by the current user"""
        return CartoonImage.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )

    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == "create":
            return CartoonImageCreateSerializer
        return CartoonImageSerializer

    @swagger_auto_schema(
        operation_description="""
        사용자의 모든 만화 변환 이미지 목록을 반환합니다.
        
        결과는 생성 시간의 역순으로 정렬되어 최근에 생성된 이미지가 먼저 표시됩니다.
        각 이미지 항목에는 원본 이미지, 변환된 이미지, 상태, 사용된 모델 등의 정보가 포함됩니다.
        """,
        responses={
            200: openapi.Response(
                description="변환된 이미지 목록이 성공적으로 반환되었습니다",
                schema=CartoonImageSerializer(many=True),
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "user": "username",
                            "original_image": "/media/cartoon_images/original.jpg",
                            "converted_image": "/media/cartoon_images/original_cartoon.jpg",
                            "prompt": "만화 스타일로 변환해주세요",
                            "model_used": "cartoon_model_v1",
                            "status": "completed",
                            "created_at": "2023-06-15T10:30:00Z",
                            "updated_at": "2023-06-15T10:35:00Z",
                        }
                    ]
                },
            ),
            401: openapi.Response(
                description="인증되지 않은 사용자",
                examples={
                    "application/json": {
                        "detail": "자격 인증데이터(authentication credentials)가 제공되지 않았습니다."
                    }
                },
            ),
        },
        tags=["ai 이미지 변환"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""
        새로운 이미지 변환 작업을 생성합니다.
        
        사용자가 원본 이미지를 업로드하면 비동기적으로 이미지 변환이 시작됩니다.
        변환 프로세스는 백그라운드에서 실행되며, 변환이 완료될 때까지 상태는 'pending'에서 'processing'을 거쳐 'completed'로 변경됩니다.
        변환 중 오류가 발생하면 상태는 'failed'로 설정됩니다.
        """,
        request_body=CartoonImageCreateSerializer,
        manual_parameters=[
            openapi.Parameter(
                name="original_image",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="변환할 원본 이미지 파일 (지원 형식: JPG, PNG, WEBP)",
            ),
            openapi.Parameter(
                name="prompt",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="변환 과정에서 사용할 추가 지시사항 (예: '스튜디오 지브리 스타일로 변환해주세요')",
                example="애니메이션 캐릭터처럼 만들어주세요",
            ),
            openapi.Parameter(
                name="model_used",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                default="default_model",
                description="이미지 변환에 사용할 AI 모델 (사용 가능: default_model, anime_style, pixel_art, cartoon_realistic)",
                example="anime_style",
            ),
        ],
        responses={
            201: openapi.Response(
                description="이미지가 성공적으로 업로드되고 변환이 시작되었습니다",
                schema=CartoonImageSerializer,
                examples={
                    "application/json": {
                        "id": 1,
                        "user": "username",
                        "original_image": "/media/cartoon_images/original.jpg",
                        "converted_image": None,
                        "prompt": "애니메이션 캐릭터처럼 만들어주세요",
                        "model_used": "anime_style",
                        "status": "pending",
                        "created_at": "2023-06-15T10:30:00Z",
                        "updated_at": "2023-06-15T10:30:00Z",
                    }
                },
            ),
            400: openapi.Response(
                description="잘못된 요청",
                examples={
                    "application/json": {
                        "original_image": ["이 필드는 필수 항목입니다."]
                    }
                },
            ),
            401: "인증되지 않은 사용자",
        },
        tags=["ai 이미지 변환"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Save the user and start the conversion process"""
        instance = serializer.save(user=self.request.user)

        # Start conversion in background thread to avoid blocking the response
        thread = threading.Thread(target=convert_to_cartoon, args=(instance,))
        thread.start()

    @swagger_auto_schema(
        operation_description="""
        지정된 ID의 만화 이미지 세부 정보를 조회합니다.
        
        변환 상태, 원본 및 변환된 이미지 URL, 사용자가 제공한 프롬프트 등의 정보를 포함합니다.
        사용자는 자신이 생성한 이미지만 조회할 수 있습니다.
        """,
        responses={
            200: openapi.Response(
                description="이미지 세부 정보 조회 성공",
                schema=CartoonImageSerializer(),
                examples={
                    "application/json": {
                        "id": 1,
                        "user": "username",
                        "original_image": "/media/cartoon_images/original.jpg",
                        "converted_image": "/media/cartoon_images/original_cartoon.jpg",
                        "prompt": "애니메이션 캐릭터처럼 만들어주세요",
                        "model_used": "anime_style",
                        "status": "completed",
                        "created_at": "2023-06-15T10:30:00Z",
                        "updated_at": "2023-06-15T10:35:00Z",
                    }
                },
            ),
            404: openapi.Response(
                description="존재하지 않는 이미지",
                examples={"application/json": {"detail": "찾을 수 없습니다."}},
            ),
            401: "인증되지 않은 사용자",
        },
        tags=["ai 이미지 변환"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""
        이미지 변환 작업을 삭제합니다.
        
        원본 이미지와 변환된 이미지 파일이 모두 삭제됩니다.
        사용자는 자신이 생성한 이미지만 삭제할 수 있습니다.
        """,
        responses={
            204: openapi.Response(description="이미지가 성공적으로 삭제되었습니다"),
            404: openapi.Response(
                description="존재하지 않는 이미지",
                examples={"application/json": {"detail": "찾을 수 없습니다."}},
            ),
            401: "인증되지 않은 사용자",
        },
        tags=["ai 이미지 변환"],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""
        기존 이미지의 변환을 다시 실행합니다.
        
        이미 변환된 이미지가 있더라도 다시 변환 작업을 수행합니다.
        상태는 다시 'processing'으로 변경되고, 변환이 완료되면 'completed'로 업데이트됩니다.
        동일한 원본 이미지와 프롬프트를 사용하지만 다른 결과를 얻을 수 있습니다.
        """,
        responses={
            202: openapi.Response(
                description="변환 작업이 다시 시작되었습니다",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "status": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="상태 메시지",
                            example="conversion started",
                        )
                    },
                ),
                examples={"application/json": {"status": "conversion started"}},
            ),
            404: openapi.Response(
                description="존재하지 않는 이미지",
                examples={"application/json": {"detail": "찾을 수 없습니다."}},
            ),
            401: "인증되지 않은 사용자",
        },
        tags=["ai 이미지 변환"],
    )
    @action(detail=True, methods=["post"])
    def regenerate(self, request, pk=None):
        """Regenerate the cartoon image"""
        image = get_object_or_404(CartoonImage, id=pk, user=request.user)

        # Start conversion in background thread
        thread = threading.Thread(target=convert_to_cartoon, args=(image,))
        thread.start()

        return Response(
            {"status": "conversion started"}, status=status.HTTP_202_ACCEPTED
        )


def process_pending_images():
    """Process any pending images - can be called by a scheduled task"""
    pending_images = CartoonImage.objects.filter(
        Q(status="pending") | Q(status="failed")
    )

    for image in pending_images:
        # Start conversion in background thread
        thread = threading.Thread(target=convert_to_cartoon, args=(image,))
        thread.start()
