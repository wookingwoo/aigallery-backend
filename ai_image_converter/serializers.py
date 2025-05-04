from rest_framework import serializers
from .models import CartoonImage


class CartoonImageSerializer(serializers.ModelSerializer):
    """Serializer for cartoon image model"""

    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CartoonImage
        fields = [
            "id",
            "user",
            "original_image",
            "converted_image",
            "prompt",
            "model_used",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "original_image",
            "converted_image",
            "prompt",
            "model_used",
            "status",
            "created_at",
            "updated_at",
        ]


class CartoonImageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating cartoon image conversions"""

    class Meta:
        model = CartoonImage
        fields = ["original_image", "prompt", "model_used"]

    def create(self, validated_data):
        # Set current user as the owner
        user = self.context["request"].user
        validated_data["user"] = user
        return super().create(validated_data)
