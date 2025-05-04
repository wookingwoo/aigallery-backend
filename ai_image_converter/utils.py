import os
from django.core.files.base import ContentFile
import logging
import base64
from openai import OpenAI

logger = logging.getLogger(__name__)


def convert_to_ai_image(image_instance):
    """
    Convert an image using OpenAI's image editing API.

    Args:
        image_instance: AIImage instance containing the original image

    Returns:
        bool: True if conversion was successful, False otherwise
    """
    try:
        # Update status to processing
        image_instance.status = "processing"
        image_instance.save(update_fields=["status"])

        # Get original image path
        original_image_path = image_instance.original_image.path

        # Get API key from environment variables
        api_key = os.environ.get("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)

        # Get the prompt from the image instance
        ghibli_prompt = "Turn this photo into studio ghibli style art with vibrant colors, dream-like landscapes and that signature Miyazaki charm."
        prompt = image_instance.prompt or ghibli_prompt

        # Call OpenAI API to convert the image
        result = client.images.edit(
            model="gpt-image-1",
            image=[
                open(original_image_path, "rb"),
            ],
            prompt=prompt,
        )

        # Get the base64 image data and decode it
        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        # Create a unique filename for the converted image
        filename = os.path.basename(image_instance.original_image.name)
        name, ext = os.path.splitext(filename)
        converted_filename = f"{name}_ai{ext}"

        # Save the converted image to the model
        image_instance.converted_image.save(
            converted_filename, ContentFile(image_bytes), save=False
        )

        # Update status to completed
        image_instance.status = "completed"
        image_instance.save(update_fields=["converted_image", "status", "updated_at"])

        return True
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error converting image: {error_message}")

        # Save error message to database
        image_instance.status = "failed"
        image_instance.error_message = error_message
        image_instance.save(update_fields=["status", "error_message"])

        return False
