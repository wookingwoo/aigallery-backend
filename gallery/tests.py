from django.test import TestCase
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import User, Friendship
from .models import Image, Comment, Like
import os
import tempfile
from PIL import Image as PILImage

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user():
    def _create_user(email='test@example.com', password='testpassword123', **kwargs):
        return User.objects.create_user(
            email=email,
            password=password,
            first_name=kwargs.get('first_name', 'Test'),
            last_name=kwargs.get('last_name', 'User'),
            **kwargs
        )
    return _create_user

@pytest.fixture
def create_test_image():
    # Create a temporary image file for testing
    def _create_test_image(filename='test.jpg', size=(100, 100), color='blue'):
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        img = PILImage.new('RGB', size, color=color)
        img.save(tmp_file.name)
        tmp_file.close()
        
        # Open the file and create a SimpleUploadedFile
        with open(tmp_file.name, 'rb') as f:
            file_content = f.read()
        
        # Delete the temporary file
        os.unlink(tmp_file.name)
        
        return SimpleUploadedFile(filename, file_content, content_type='image/jpeg')
    
    return _create_test_image

@pytest.mark.django_db
class TestImageModel:
    def test_create_image(self, create_user, create_test_image):
        user = create_user()
        test_image = create_test_image()
        
        image = Image.objects.create(
            user=user,
            image=test_image,
            title='Test Image',
            description='Test description',
            visibility='public'
        )
        
        assert image.title == 'Test Image'
        assert image.description == 'Test description'
        assert image.visibility == 'public'
        assert image.user == user

@pytest.mark.django_db
class TestImageAPI:
    def test_create_image(self, api_client, create_user, create_test_image):
        user = create_user()
        api_client.force_authenticate(user=user)
        
        test_image = create_test_image()
        url = reverse('image-list')
        
        data = {
            'title': 'API Test Image',
            'description': 'Image created via API',
            'visibility': 'public',
            'image': test_image
        }
        
        response = api_client.post(url, data, format='multipart')
        assert response.status_code == status.HTTP_201_CREATED
        assert Image.objects.filter(title='API Test Image').exists()
    
    def test_list_images(self, api_client, create_user, create_test_image):
        user1 = create_user(email='user1@example.com')
        user2 = create_user(email='user2@example.com')
        
        # Create friendship
        Friendship.objects.create(user=user1, friend=user2)
        
        # Create images for both users
        test_image1 = create_test_image(filename='user1.jpg')
        test_image2 = create_test_image(filename='user2_public.jpg')
        test_image3 = create_test_image(filename='user2_friends.jpg')
        
        Image.objects.create(
            user=user1,
            image=test_image1,
            title='User 1 Image',
            visibility='public'
        )
        
        Image.objects.create(
            user=user2,
            image=test_image2,
            title='User 2 Public Image',
            visibility='public'
        )
        
        Image.objects.create(
            user=user2,
            image=test_image3,
            title='User 2 Friends Image',
            visibility='friends'
        )
        
        # User 1 should see all images
        api_client.force_authenticate(user=user1)
        url = reverse('image-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        
        # User 1 should see friend images
        url = reverse('image-friend-images')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        # User 2 should not see User 1's friends-only images since no friendship in that direction
        api_client.force_authenticate(user=user2)
        url = reverse('image-friend-images')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

@pytest.mark.django_db
class TestCommentAPI:
    def test_create_comment(self, api_client, create_user, create_test_image):
        user = create_user()
        test_image = create_test_image()
        
        # Create image
        image = Image.objects.create(
            user=user,
            image=test_image,
            title='Test Image',
            visibility='public'
        )
        
        api_client.force_authenticate(user=user)
        url = reverse('comment-list')
        
        data = {
            'image': image.id,
            'text': 'Test comment'
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Comment.objects.filter(image=image, text='Test comment').exists()

@pytest.mark.django_db
class TestLikeAPI:
    def test_like_unlike_image(self, api_client, create_user, create_test_image):
        user = create_user()
        test_image = create_test_image()
        
        # Create image
        image = Image.objects.create(
            user=user,
            image=test_image,
            title='Test Image',
            visibility='public'
        )
        
        api_client.force_authenticate(user=user)
        
        # Like the image
        url = reverse('like-list')
        data = {'image': image.id}
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Like.objects.filter(user=user, image=image).exists()
        
        # Try to like again - should fail
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Unlike the image
        url = reverse('like-unlike')
        response = api_client.delete(f"{url}?image={image.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Like.objects.filter(user=user, image=image).exists()
