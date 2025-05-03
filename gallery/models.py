from django.db import models
from django.conf import settings


class Image(models.Model):
    """Model for user uploaded images."""
    
    VISIBILITY_CHOICES = (
        ('public', 'Public'),
        ('friends', 'Friends Only'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='gallery_images/')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']


class Comment(models.Model):
    """Model for comments on images."""
    
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.user.email} on {self.image.title}"
    
    class Meta:
        ordering = ['created_at']


class Like(models.Model):
    """Model for likes on images."""
    
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('image', 'user')
    
    def __str__(self):
        return f"Like by {self.user.email} on {self.image.title}"
