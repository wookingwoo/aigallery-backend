# Generated by Django 5.2 on 2025-05-04 10:22

import ai_image_converter.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CartoonImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_image', models.ImageField(upload_to=ai_image_converter.models.get_image_upload_path)),
                ('converted_image', models.ImageField(blank=True, null=True, upload_to=ai_image_converter.models.get_image_upload_path)),
                ('prompt', models.TextField(blank=True, null=True)),
                ('model_used', models.CharField(default='default_model', max_length=100)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cartoon_images', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
