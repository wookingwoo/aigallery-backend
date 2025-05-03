from rest_framework import serializers
from .models import Image, Comment, Like
from django.contrib.auth import get_user_model

User = get_user_model()


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for image comments."""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ('id', 'image', 'user', 'user_email', 'user_name', 'text', 'created_at')
        read_only_fields = ('user', 'created_at')
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class LikeSerializer(serializers.ModelSerializer):
    """Serializer for image likes."""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = Like
        fields = ('id', 'image', 'user', 'user_email', 'created_at')
        read_only_fields = ('user', 'created_at')


class ImageSerializer(serializers.ModelSerializer):
    """Serializer for user images."""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    user_name = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Image
        fields = ('id', 'user', 'user_email', 'user_name', 'image', 'title', 'description', 
                  'visibility', 'created_at', 'updated_at', 'comments', 'likes_count', 'is_liked')
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False 