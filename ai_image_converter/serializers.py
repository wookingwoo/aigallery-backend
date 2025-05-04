from rest_framework import serializers
from .models import AIImage


class AIImageSerializer(serializers.ModelSerializer):
    """Serializer for AI image conversions"""

    user = serializers.SerializerMethodField()

    class Meta:
        model = AIImage
        fields = [
            "id",
            "user",
            "original_image",
            "converted_image",
            "prompt",
            "model_used",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "original_image",
            "converted_image",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]

    def get_user(self, obj):
        """Return username as user representation"""
        return obj.user.username


class AIImageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating AI image conversions"""

    class Meta:
        model = AIImage
        fields = ["original_image", "prompt", "model_used"]

    def create(self, validated_data):
        # Set current user as the owner
        user = self.context["request"].user
        validated_data["user"] = user
        return super().create(validated_data)
