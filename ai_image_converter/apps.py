from django.apps import AppConfig


class AiImageConverterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai_image_converter"
    verbose_name = "AI Image Converter"

    def ready(self):
        """Initialize app when Django starts"""
        # Import signals or perform initialization tasks here
        pass
