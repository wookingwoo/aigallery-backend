from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model."""

    username = None
    email = models.EmailField(_("email address"), unique=True)
    profile_image = models.ImageField(
        upload_to="profile_images/", null=True, blank=True
    )
    bio = models.TextField(blank=True)
    credits = models.PositiveIntegerField(
        default=10, help_text="사용자가 가진 크레딧 수"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def use_credit(self, amount=1, reason="AI 이미지 변환"):
        """
        사용자의 크레딧을 사용합니다.

        Args:
            amount (int): 사용할 크레딧 양 (기본값: 1)
            reason (str): 크레딧 사용 이유

        Returns:
            bool: 크레딧 사용 성공 여부

        Raises:
            ValueError: 크레딧이 부족한 경우
        """
        if self.credits < amount:
            return False

        self.credits -= amount
        self.save(update_fields=["credits"])

        # 크레딧 사용 내역 기록
        CreditUsage.objects.create(user=self, amount=amount, reason=reason)

        return True

    def add_credits(self, amount, reason="크레딧 충전"):
        """
        사용자에게 크레딧을 추가합니다.

        Args:
            amount (int): 추가할 크레딧 양
            reason (str): 크레딧 추가 이유
        """
        self.credits += amount
        self.save(update_fields=["credits"])

        # 크레딧 추가 내역 기록
        CreditUsage.objects.create(
            user=self, amount=amount, is_usage=False, reason=reason
        )

        return True


class Friendship(models.Model):
    """Model representing friendship between users."""

    user = models.ForeignKey(User, related_name="friendships", on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name="friend_of", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "friend")

    def __str__(self):
        return f"{self.user.email} is friends with {self.friend.email}"


class FriendRequest(models.Model):
    """Model representing friend requests between users."""

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    )

    sender = models.ForeignKey(
        User, related_name="sent_friend_requests", on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        User, related_name="received_friend_requests", on_delete=models.CASCADE
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("sender", "receiver")

    def __str__(self):
        return f"{self.sender.email} -> {self.receiver.email} ({self.status})"

    def accept(self):
        """Accept friend request and create friendship."""
        if self.status == "pending":
            # Create bi-directional friendship
            Friendship.objects.create(user=self.sender, friend=self.receiver)
            Friendship.objects.create(user=self.receiver, friend=self.sender)
            self.status = "accepted"
            self.save()

    def reject(self):
        """Reject friend request."""
        if self.status == "pending":
            self.status = "rejected"
            self.save()


class CreditUsage(models.Model):
    """
    크레딧 사용 및 충전 내역
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="credit_usages"
    )
    amount = models.PositiveIntegerField(help_text="사용하거나 충전한 크레딧 양")
    is_usage = models.BooleanField(
        default=True, help_text="사용인지 충전인지 여부 (True: 사용, False: 충전)"
    )
    reason = models.CharField(max_length=255, help_text="크레딧 변동 이유")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        action = "사용" if self.is_usage else "충전"
        return f"{self.user.email}의 크레딧 {action}: {self.amount}개 ({self.reason})"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "크레딧 사용 내역"
        verbose_name_plural = "크레딧 사용 내역"
