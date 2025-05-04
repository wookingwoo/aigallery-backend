from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Friendship, FriendRequest, User, CreditUsage
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer with additional user info"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token["email"] = user.email
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name

        return token


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "profile_image",
            "bio",
            "credits",
        )
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "password": {"write_only": True},
        }
        read_only_fields = ["id", "credits"]

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
        )

        if "profile_image" in validated_data:
            user.profile_image = validated_data["profile_image"]

        if "bio" in validated_data:
            user.bio = validated_data["bio"]

        user.save()
        return user

    def update(self, instance, validated_data):
        if "password" in validated_data:
            password = validated_data.pop("password")
            instance.set_password(password)

        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("현재 비밀번호가 일치하지 않습니다.")
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profiles."""

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "profile_image", "bio")
        read_only_fields = ("email",)


class FriendshipSerializer(serializers.ModelSerializer):
    """Serializer for friendships."""

    friend = UserSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = ("id", "friend", "created_at")
        read_only_fields = ("created_at",)


class FriendRequestSerializer(serializers.ModelSerializer):
    """Serializer for friend requests."""

    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    receiver_email = serializers.EmailField(write_only=True)

    class Meta:
        model = FriendRequest
        fields = (
            "id",
            "sender",
            "receiver",
            "receiver_email",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("sender", "receiver", "status", "created_at", "updated_at")

    def create(self, validated_data):
        sender = self.context["request"].user
        receiver_email = validated_data.pop("receiver_email")

        try:
            receiver = User.objects.get(email=receiver_email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"receiver_email": "해당 이메일을 가진 사용자가 존재하지 않습니다."}
            )

        if sender == receiver:
            raise serializers.ValidationError(
                {"receiver_email": "자신에게 친구 요청을 보낼 수 없습니다."}
            )

        if FriendRequest.objects.filter(
            sender=sender, receiver=receiver, status="pending"
        ).exists():
            raise serializers.ValidationError(
                {"receiver_email": "이미 해당 사용자에게 친구 요청을 보냈습니다."}
            )

        if Friendship.objects.filter(user=sender, friend=receiver).exists():
            raise serializers.ValidationError(
                {"receiver_email": "이미 해당 사용자와 친구입니다."}
            )

        friend_request = FriendRequest.objects.create(
            sender=sender, receiver=receiver, status="pending"
        )

        return friend_request


class TokenObtainPairResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()


class CreditUsageSerializer(serializers.ModelSerializer):
    """크레딧 사용 내역 시리얼라이저"""

    class Meta:
        model = CreditUsage
        fields = ["id", "amount", "is_usage", "reason", "created_at"]
        read_only_fields = ["id", "amount", "is_usage", "reason", "created_at"]


class CreditChargeSerializer(serializers.Serializer):
    """크레딧 충전 시리얼라이저"""

    amount = serializers.IntegerField(
        min_value=1, required=True, help_text="충전할 크레딧 수"
    )
    payment_method = serializers.ChoiceField(
        choices=[
            ("card", "신용카드"),
            ("bank", "계좌이체"),
            ("virtual", "가상 결제(테스트용)"),
        ],
        default="virtual",
        help_text="결제 수단",
    )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("충전할 크레딧은 1개 이상이어야 합니다.")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        amount = validated_data.get("amount")

        # 실제 환경에서는 여기서 결제 처리를 수행
        # 이 예제에서는 바로 크레딧을 추가

        user.add_credits(
            amount, reason=f"{validated_data.get('payment_method')}를 통한 크레딧 충전"
        )

        return {
            "user": user,
            "amount": amount,
            "payment_method": validated_data.get("payment_method"),
            "status": "success",
        }
