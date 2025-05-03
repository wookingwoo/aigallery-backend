from django.shortcuts import render
from rest_framework import viewsets, status, permissions, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Image, Comment, Like
from .serializers import ImageSerializer, CommentSerializer, LikeSerializer
from users.models import Friendship
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user


class VisibilityPermission(permissions.BasePermission):
    """
    Custom permission to handle image visibility based on friendship status.
    """

    def has_object_permission(self, request, view, obj):
        # Owner can always access their own images
        if obj.user == request.user:
            return True

        # For public images, anyone can access
        if obj.visibility == "public":
            return True

        # For friends-only images, check if the user is a friend
        if obj.visibility == "friends":
            return Friendship.objects.filter(
                user=obj.user, friend=request.user
            ).exists()

        return False


class ImageViewSet(viewsets.ModelViewSet):
    """ViewSet for handling image operations."""

    serializer_class = ImageSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsOwnerOrReadOnly,
        VisibilityPermission,
    ]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        """
        Return images the user is allowed to see:
        - All public images
        - All images of friends if they are "friends-only"
        - All own images
        """
        user = self.request.user

        # Get IDs of all friends
        friend_ids = Friendship.objects.filter(user=user).values_list(
            "friend_id", flat=True
        )

        # Return all images that are:
        # 1. Public
        # 2. User's own images
        # 3. Friend's images with "friends-only" visibility
        return Image.objects.filter(
            Q(visibility="public")
            | Q(user=user)
            | Q(user_id__in=friend_ids, visibility="friends")
        )

    @swagger_auto_schema(
        operation_description="이미지를 업로드하고 생성합니다.",
        manual_parameters=[
            openapi.Parameter(
                name="image",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="업로드할 이미지 파일",
            ),
            openapi.Parameter(
                name="title",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="이미지 제목",
            ),
            openapi.Parameter(
                name="description",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="이미지 설명",
            ),
            openapi.Parameter(
                name="visibility",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="이미지 공개 설정 (public 또는 friends)",
                enum=["public", "friends"],
            ),
        ],
        responses={
            201: openapi.Response(
                description="이미지가 성공적으로 생성됨", schema=ImageSerializer
            ),
            400: "잘못된 입력",
            403: "권한 없음",
        },
    )
    def create(self, request, *args, **kwargs):
        """Set the user when creating an image."""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Set the user when creating an image."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def my_images(self, request):
        """Retrieve only the authenticated user's images."""
        images = Image.objects.filter(user=request.user)
        page = self.paginate_queryset(images)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            images, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def friend_images(self, request):
        """Retrieve images from friends."""
        # Get IDs of all friends
        friend_ids = Friendship.objects.filter(user=request.user).values_list(
            "friend_id", flat=True
        )

        # Get all images from friends that the user is allowed to see
        images = Image.objects.filter(user_id__in=friend_ids).filter(
            Q(visibility="public") | Q(visibility="friends")
        )

        page = self.paginate_queryset(images)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            images, many=True, context={"request": request}
        )
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for handling comments."""

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Return comments for images the user can see."""
        return Comment.objects.filter(image__in=self.get_visible_images())

    def get_visible_images(self):
        """Get all images the user can see."""
        user = self.request.user
        friend_ids = Friendship.objects.filter(user=user).values_list(
            "friend_id", flat=True
        )

        return Image.objects.filter(
            Q(visibility="public")
            | Q(user=user)
            | Q(user_id__in=friend_ids, visibility="friends")
        )

    def perform_create(self, serializer):
        """Set the user when creating a comment."""
        image_id = self.request.data.get("image")
        image = Image.objects.get(id=image_id)

        # Check if user has permission to comment (can see the image)
        if not VisibilityPermission().has_object_permission(self.request, self, image):
            return Response(
                {"detail": "You do not have permission to comment on this image."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.save(user=self.request.user)


class LikeViewSet(viewsets.ModelViewSet):
    """ViewSet for handling likes."""

    http_method_names = ["get", "post", "delete"]  # patch 메서드 사용 안함
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return likes for the user."""
        return Like.objects.filter(user=self.request.user)

    def get_visible_images(self):
        """Get all images the user can see."""
        user = self.request.user
        friend_ids = Friendship.objects.filter(user=user).values_list(
            "friend_id", flat=True
        )

        return Image.objects.filter(
            Q(visibility="public")
            | Q(user=user)
            | Q(user_id__in=friend_ids, visibility="friends")
        )

    def create(self, request, *args, **kwargs):
        """Create a like if it doesn't exist already."""
        image_id = request.data.get("image")
        image = Image.objects.get(id=image_id)

        # Check if user can see the image
        if not VisibilityPermission().has_object_permission(request, self, image):
            return Response(
                {"detail": "You do not have permission to like this image."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if like already exists
        if Like.objects.filter(user=request.user, image_id=image_id).exists():
            return Response(
                {"detail": "You have already liked this image."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create the like
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="이미지에 대한 좋아요를 취소합니다. (image id 기반)",
        manual_parameters=[
            openapi.Parameter(
                name="image",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="좋아요를 취소할 이미지 ID",
            )
        ],
        responses={
            204: "좋아요가 성공적으로 취소됨",
            400: "잘못된 요청 (이미지 ID 누락 또는 좋아요가 없음)",
            403: "권한 없음",
        },
    )
    @action(detail=False, methods=["delete"])
    def unlike(self, request):
        """Remove a like from an image."""
        image_id = request.query_params.get("image")
        if not image_id:
            return Response(
                {"detail": "Image ID is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        like = Like.objects.filter(user=request.user, image_id=image_id).first()
        if not like:
            return Response(
                {"detail": "You have not liked this image."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        like.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
