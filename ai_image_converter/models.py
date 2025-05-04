from django.db import models
from django.conf import settings
import os
import uuid


def get_image_upload_path(instance, filename):
    """Generate a unique file path for the uploaded image"""
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("ai_images", filename)


class AIImage(models.Model):
    """
    ai 이미지 변환을 저장하는 모델

    이 모델은 사용자가 업로드한 원본 이미지와 AI 기술을 사용하여 만화 스타일로 변환된
    이미지, 변환 과정에 사용된 프롬프트와 모델 정보, 그리고 현재 변환 상태를 저장합니다.

    상태 코드 설명:
    - pending: 변환 대기 중
    - processing: 변환 처리 중
    - completed: 변환 완료
    - failed: 변환 실패
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_images",
        help_text="이미지를 업로드한 사용자",
    )
    original_image = models.ImageField(
        upload_to=get_image_upload_path,
        help_text="변환할 원본 이미지",
    )
    converted_image = models.ImageField(
        upload_to=get_image_upload_path,
        blank=True,
        null=True,
        help_text="만화 스타일로 변환된 이미지",
    )
    prompt = models.TextField(
        blank=True,
        null=True,
        help_text="이미지 변환을 위한 추가 지시사항 (예: '스튜디오 지브리 스타일로 변환해주세요')",
    )
    model_used = models.CharField(
        max_length=100,
        default="default_model",
        help_text="변환에 사용된 AI 모델 (예: default_model, anime_style, pixel_art, cartoon_realistic)",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
        help_text="현재 변환 상태 (pending: 대기 중, processing: 처리 중, completed: 완료, failed: 실패)",
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="ai 이미지 생성 실패 시 에러 메시지",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="변환 요청이 생성된 시간",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="마지막으로 변환 상태가 업데이트된 시간",
    )

    def __str__(self):
        return f"AI image {self.id} by {self.user.username}"
