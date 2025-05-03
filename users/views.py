from django.shortcuts import render
from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import User, Friendship
from .serializers import UserSerializer, UserProfileSerializer, FriendshipSerializer
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


@swagger_auto_schema(
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["email", "first_name", "last_name", "password"],
        properties={
            "email": openapi.Schema(
                type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL
            ),
            "first_name": openapi.Schema(type=openapi.TYPE_STRING),
            "last_name": openapi.Schema(type=openapi.TYPE_STRING),
            "password": openapi.Schema(
                type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD
            ),
            "profile_image": openapi.Schema(type=openapi.TYPE_FILE),
            "bio": openapi.Schema(type=openapi.TYPE_STRING),
        },
    ),
    responses={201: UserSerializer, 400: "Bad Request"},
)
class RegisterView(generics.CreateAPIView):
    """View for user registration."""

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user management."""

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ["update", "partial_update", "me"]:
            return UserProfileSerializer
        return UserSerializer

    @swagger_auto_schema(
        methods=["get"],
        operation_description="Retrieve the current user's profile",
        responses={200: UserProfileSerializer},
    )
    @swagger_auto_schema(
        methods=["put", "patch"],
        operation_description="Update the current user's profile",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "first_name": openapi.Schema(type=openapi.TYPE_STRING),
                "last_name": openapi.Schema(type=openapi.TYPE_STRING),
                "profile_image": openapi.Schema(type=openapi.TYPE_FILE),
                "bio": openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={200: UserProfileSerializer, 400: "Bad Request"},
    )
    @action(
        detail=False,
        methods=["get", "put", "patch"],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """Get or update current user's profile."""
        user = request.user
        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FriendshipViewSet(viewsets.ModelViewSet):
    """ViewSet for friendship management."""

    serializer_class = FriendshipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return friendships for the current user."""
        return Friendship.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["friend"],
            properties={
                "friend": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID of the user to establish friendship with",
                )
            },
        ),
        responses={
            201: FriendshipSerializer,
            400: "Friendship already exists",
            404: "User not found",
        },
    )
    def create(self, request, *args, **kwargs):
        """Create a new friendship."""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Create a new friendship."""
        friend_id = self.request.data.get("friend")
        friend = get_object_or_404(User, id=friend_id)

        # Check if friendship already exists
        if Friendship.objects.filter(user=self.request.user, friend=friend).exists():
            return Response(
                {"detail": "Friendship already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create the friendship
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        method="get",
        operation_description="Find users that are not friends with the current user",
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search string to filter users by email, first name, or last name",
                type=openapi.TYPE_STRING,
                required=False,
            )
        ],
        responses={
            200: openapi.Response(
                description="List of users that are not friends",
                schema=UserProfileSerializer(many=True),
            )
        },
    )
    @action(detail=False, methods=["get"])
    def find_users(self, request):
        """Find users that are not friends with the current user."""
        search_query = request.query_params.get("search", "")

        # Get all friend IDs
        friend_ids = Friendship.objects.filter(user=request.user).values_list(
            "friend_id", flat=True
        )

        # Find users that are not friends and match search query
        users = User.objects.exclude(id=request.user.id).exclude(id__in=friend_ids)

        if search_query:
            users = users.filter(
                Q(email__icontains=search_query)
                | Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
            )

        page = self.paginate_queryset(users)
        if page is not None:
            serializer = UserProfileSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = UserProfileSerializer(users, many=True)
        return Response(serializer.data)
