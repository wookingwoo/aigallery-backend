from django.contrib import admin
from .models import AIImage


@admin.register(AIImage)
class AIImageAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "model_used", "status", "created_at")
    list_filter = ("status", "model_used", "created_at")
    search_fields = ("user__username", "prompt")
    readonly_fields = ("created_at", "updated_at")
