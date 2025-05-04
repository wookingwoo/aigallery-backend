from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, CreditUsage, Friendship, FriendRequest


# Register your models here.
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model"""

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "profile_image", "bio", "credits")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    list_display = ("email", "first_name", "last_name", "credits", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)


class CreditUsageAdmin(admin.ModelAdmin):
    """Admin for CreditUsage model"""

    list_display = ("user", "amount", "is_usage", "reason", "created_at")
    list_filter = ("is_usage", "created_at")
    search_fields = ("user__email", "reason")
    date_hierarchy = "created_at"


class FriendshipAdmin(admin.ModelAdmin):
    """Admin for Friendship model"""

    list_display = ("user", "friend", "created_at")
    search_fields = ("user__email", "friend__email")


class FriendRequestAdmin(admin.ModelAdmin):
    """Admin for FriendRequest model"""

    list_display = ("sender", "receiver", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("sender__email", "receiver__email")


admin.site.register(User, UserAdmin)
admin.site.register(CreditUsage, CreditUsageAdmin)
admin.site.register(Friendship, FriendshipAdmin)
admin.site.register(FriendRequest, FriendRequestAdmin)
