from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Friendship

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'password', 'profile_image', 'bio')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        
        if 'profile_image' in validated_data:
            user.profile_image = validated_data['profile_image']
        
        if 'bio' in validated_data:
            user.bio = validated_data['bio']
            
        user.save()
        return user
        
    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        
        return super().update(instance, validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profiles."""
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'profile_image', 'bio')
        read_only_fields = ('email',)


class FriendshipSerializer(serializers.ModelSerializer):
    """Serializer for friendships."""
    
    friend_details = UserProfileSerializer(source='friend', read_only=True)
    
    class Meta:
        model = Friendship
        fields = ('id', 'friend', 'friend_details', 'created_at')
        read_only_fields = ('created_at',) 
        
class TokenObtainPairResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    
class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()