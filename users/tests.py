from django.test import TestCase
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from .models import User, Friendship

# Create your tests here.

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

@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self, create_user):
        user = create_user()
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.check_password('testpassword123')
        assert not user.is_staff
        assert not user.is_superuser
    
    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpassword123'
        )
        assert superuser.email == 'admin@example.com'
        assert superuser.is_staff
        assert superuser.is_superuser

@pytest.mark.django_db
class TestUserAPI:
    def test_register_user(self, api_client):
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email='newuser@example.com').exists()
    
    def test_login_user(self, api_client, create_user):
        user = create_user()
        url = reverse('token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_me_endpoint(self, api_client, create_user):
        user = create_user()
        api_client.force_authenticate(user=user)
        url = reverse('user-me')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email
        
        # Test update profile
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'New bio text'
        }
        response = api_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == 'Updated'
        assert user.last_name == 'Name'
        assert user.bio == 'New bio text'

@pytest.mark.django_db
class TestFriendshipAPI:
    def test_create_friendship(self, api_client, create_user):
        user1 = create_user(email='user1@example.com')
        user2 = create_user(email='user2@example.com')
        
        api_client.force_authenticate(user=user1)
        url = reverse('friendship-list')
        data = {'friend': user2.id}
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Friendship.objects.filter(user=user1, friend=user2).exists()
    
    def test_list_friendships(self, api_client, create_user):
        user1 = create_user(email='user1@example.com')
        user2 = create_user(email='user2@example.com')
        user3 = create_user(email='user3@example.com')
        
        Friendship.objects.create(user=user1, friend=user2)
        Friendship.objects.create(user=user1, friend=user3)
        
        api_client.force_authenticate(user=user1)
        url = reverse('friendship-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    def test_find_users(self, api_client, create_user):
        user1 = create_user(email='user1@example.com')
        user2 = create_user(email='user2@example.com')
        user3 = create_user(email='friend@example.com')
        
        # Create friendship between user1 and user3
        Friendship.objects.create(user=user1, friend=user3)
        
        api_client.force_authenticate(user=user1)
        url = reverse('friendship-find-users')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Should only see user2, as user3 is already a friend
        assert len(response.data) == 1
        assert response.data[0]['email'] == 'user2@example.com'
