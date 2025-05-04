from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import User, Friendship, FriendRequest, CreditUsage
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    FriendshipSerializer,
    TokenObtainPairResponseSerializer,
    TokenRefreshResponseSerializer,
    FriendRequestSerializer,
    ChangePasswordSerializer,
    CreditUsageSerializer,
    CreditChargeSerializer,
    CustomTokenObtainPairSerializer,
)
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


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
        elif self.action == "change_password":
            return ChangePasswordSerializer
        return UserSerializer

    @swagger_auto_schema(auto_schema=None)
    def create(self, request, *args, **kwargs):
        """사용자 생성은 register 엔드포인트를 통해서만 가능하기 때문에 지원하지 않음"""
        pass

    @swagger_auto_schema(auto_schema=None)
    def update(self, request, *args, **kwargs):
        """사용자 정보 수정은 me 엔드포인트를 통해서만 가능하기 때문에 지원하지 않음"""
        pass

    @swagger_auto_schema(auto_schema=None)
    def partial_update(self, request, *args, **kwargs):
        """사용자 정보 부분 수정은 me 엔드포인트를 통해서만 가능하기 때문에 지원하지 않음"""
        pass

    @swagger_auto_schema(auto_schema=None)
    def destroy(self, request, *args, **kwargs):
        """특정 사용자 삭제 기능은 지원하지 않음"""
        pass

    @swagger_auto_schema(
        methods=["get"],
        operation_description="Retrieve the current user's profile",
        responses={200: UserProfileSerializer},
    )
    @swagger_auto_schema(
        methods=["put", "patch"],
        operation_description="""
        현재 사용자의 프로필 정보를 업데이트합니다.
        
        이 API를 통해 현재 로그인한 사용자의 프로필 정보(이름, 프로필 이미지, 자기소개 등)를 수정할 수 있습니다.
        
        - 이메일 주소는 변경할 수 없습니다.
        - 비밀번호 변경은 별도의 change_password API를 사용해야 합니다.
        - 프로필 이미지는 multipart/form-data 형식으로 전송해야 합니다.
        """,
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

    @swagger_auto_schema(
        method="post",
        operation_description="""
        현재 비밀번호를 확인하고 새 비밀번호로 변경합니다.
        
        이 API를 통해 현재 로그인한 사용자의 비밀번호를 변경할 수 있습니다.
        
        - 현재 비밀번호를 정확히 입력해야 합니다.
        - 새 비밀번호는 Django의 비밀번호 검증 규칙을 통과해야 합니다.
        - 비밀번호 변경 후 기존 토큰은 계속 유효합니다.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["old_password", "new_password"],
            properties={
                "old_password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="현재 비밀번호"
                ),
                "new_password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="새 비밀번호"
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="비밀번호가 성공적으로 변경됨",
                examples={
                    "application/json": {"detail": "Password changed successfully."}
                },
            ),
            400: openapi.Response(
                description="잘못된 요청",
                examples={
                    "application/json": {
                        "old_password": ["현재 비밀번호가 일치하지 않습니다."]
                    }
                },
            ),
        },
    )
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Change user's password."""
        user = request.user
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user.set_password(serializer.validated_data["new_password"])
            user.save()
            return Response(
                {"detail": "Password changed successfully."}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        method="post",
        operation_description="""
        현재 로그인한 사용자 계정을 비활성화(탈퇴)합니다.
        
        이 API를 통해 자신의 계정을 탈퇴할 수 있습니다.
        
        - 계정이 완전히 삭제되지는 않고 비활성화 상태로 변경됩니다.
        - 계정 비활성화 후에는 로그인할 수 없습니다.
        - 모든 친구 관계와 친구 요청은 유지됩니다.
        """,
        responses={
            200: openapi.Response(
                description="계정이 성공적으로 비활성화됨",
                examples={
                    "application/json": {"detail": "Account deactivated successfully."}
                },
            ),
        },
    )
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def deactivate(self, request):
        """Deactivate user's account."""
        user = request.user
        user.is_active = False
        user.save()
        return Response(
            {"detail": "Account deactivated successfully."}, status=status.HTTP_200_OK
        )


class FriendshipViewSet(viewsets.ModelViewSet):
    """ViewSet for friendship management."""

    serializer_class = FriendshipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return friendships for the current user."""
        return Friendship.objects.filter(user=self.request.user)

    @swagger_auto_schema(auto_schema=None)
    def create(self, request, *args, **kwargs):
        """친구 관계 생성은 친구 요청 수락을 통해서만 가능하기 때문에 지원하지 않음"""
        pass

    @swagger_auto_schema(auto_schema=None)
    def update(self, request, *args, **kwargs):
        """친구 관계는 수정할 수 없기 때문에 지원하지 않음"""
        pass

    @swagger_auto_schema(auto_schema=None)
    def partial_update(self, request, *args, **kwargs):
        """친구 관계는 수정할 수 없기 때문에 지원하지 않음"""
        pass

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


class FriendRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for friend request management."""

    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return friend requests for the current user."""
        user = self.request.user
        return FriendRequest.objects.filter(Q(sender=user) | Q(receiver=user))

    @swagger_auto_schema(auto_schema=None)
    def update(self, request, *args, **kwargs):
        """친구 요청은 accept/reject 메서드를 통해서만 수정 가능하기 때문에 지원하지 않음"""
        pass

    @swagger_auto_schema(auto_schema=None)
    def partial_update(self, request, *args, **kwargs):
        """친구 요청은 accept/reject 메서드를 통해서만 수정 가능하기 때문에 지원하지 않음"""
        pass

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["receiver"],
            properties={
                "receiver": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID of the user to send friend request to",
                )
            },
        ),
        operation_description="""
        다른 사용자에게 친구 요청을 보냅니다.
        
        이 API를 통해 다른 사용자에게 친구 요청을 보낼 수 있습니다. 상대방이 요청을 수락하면 양쪽 모두 친구 관계가 성립됩니다.
        
        - 자기 자신에게는 친구 요청을 보낼 수 없습니다.
        - 이미 친구인 사용자에게는 요청을 보낼 수 없습니다.
        - 이미 요청을 보낸 사용자에게는 중복 요청을 보낼 수 없습니다.
        - 상대방이 먼저 나에게 친구 요청을 보낸 상태라면, 이 API를 호출하면 자동으로 상대방의 요청이 수락됩니다.
        """,
        responses={
            201: openapi.Response(
                description="친구 요청이 성공적으로 생성됨",
                schema=FriendRequestSerializer,
            ),
            400: openapi.Response(
                description="잘못된 요청",
                examples={
                    "application/json": {
                        "detail": "Cannot send friend request to yourself."
                    }
                },
            ),
            404: openapi.Response(description="사용자를 찾을 수 없음"),
        },
    )
    def create(self, request, *args, **kwargs):
        """Create a new friend request."""
        receiver_id = request.data.get("receiver")
        receiver = get_object_or_404(User, id=receiver_id)

        # Don't allow sending friend request to self
        if receiver == request.user:
            return Response(
                {"detail": "Cannot send friend request to yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if friendship already exists
        if Friendship.objects.filter(user=request.user, friend=receiver).exists():
            return Response(
                {"detail": "Friendship already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if there's already a pending request
        existing_request = FriendRequest.objects.filter(
            sender=request.user, receiver=receiver, status="pending"
        ).first()

        if existing_request:
            return Response(
                {"detail": "Friend request already sent."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if there's a pending request from the receiver to the sender
        reverse_request = FriendRequest.objects.filter(
            sender=receiver, receiver=request.user, status="pending"
        ).first()

        if reverse_request:
            # Auto-accept the reverse request
            reverse_request.accept()
            return Response(
                {"detail": "Request from the user was automatically accepted."},
                status=status.HTTP_201_CREATED,
            )

        # Create new friend request
        friend_request = FriendRequest.objects.create(
            sender=request.user, receiver=receiver, status="pending"
        )

        serializer = self.get_serializer(friend_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        method="post",
        operation_description="""
        받은 친구 요청을 수락합니다.
        
        이 API를 통해 다른 사용자로부터 받은 친구 요청을 수락할 수 있습니다. 
        요청을 수락하면 양방향 친구 관계가 생성됩니다.
        
        - 요청을 받은 사용자만 수락할 수 있습니다.
        - 이미 처리된(수락/거절) 요청은 다시 수락할 수 없습니다.
        - 요청이 수락되면 양방향 친구 관계가 자동으로 생성됩니다.
        """,
        responses={
            200: openapi.Response(
                description="친구 요청이 성공적으로 수락됨",
                examples={"application/json": {"detail": "Friend request accepted."}},
            ),
            400: openapi.Response(
                description="잘못된 요청",
                examples={
                    "application/json": {
                        "detail": "You can only accept friend requests sent to you."
                    }
                },
            ),
            404: openapi.Response(description="친구 요청을 찾을 수 없음"),
        },
    )
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """Accept a friend request."""
        friend_request = self.get_object()

        # Check if the current user is the receiver
        if friend_request.receiver != request.user:
            return Response(
                {"detail": "You can only accept friend requests sent to you."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the request is still pending
        if friend_request.status != "pending":
            return Response(
                {"detail": f"This friend request is already {friend_request.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        friend_request.accept()

        return Response({"detail": "Friend request accepted."})

    @swagger_auto_schema(
        method="post",
        operation_description="""
        받은 친구 요청을 거절합니다.
        
        이 API를 통해 다른 사용자로부터 받은 친구 요청을 거절할 수 있습니다.
        
        - 요청을 받은 사용자만 거절할 수 있습니다.
        - 이미 처리된(수락/거절) 요청은 다시 거절할 수 없습니다.
        - 거절된 요청은 다시 수락할 수 없습니다.
        """,
        responses={
            200: openapi.Response(
                description="친구 요청이 성공적으로 거절됨",
                examples={"application/json": {"detail": "Friend request rejected."}},
            ),
            400: openapi.Response(
                description="잘못된 요청",
                examples={
                    "application/json": {
                        "detail": "You can only reject friend requests sent to you."
                    }
                },
            ),
            404: openapi.Response(description="친구 요청을 찾을 수 없음"),
        },
    )
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Reject a friend request."""
        friend_request = self.get_object()

        # Check if the current user is the receiver
        if friend_request.receiver != request.user:
            return Response(
                {"detail": "You can only reject friend requests sent to you."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the request is still pending
        if friend_request.status != "pending":
            return Response(
                {"detail": f"This friend request is already {friend_request.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        friend_request.reject()

        return Response({"detail": "Friend request rejected."})

    @swagger_auto_schema(
        method="get",
        operation_description="""
        현재 사용자가 받은 모든 친구 요청을 조회합니다.
        
        이 API를 통해 다른 사용자로부터 받은 모든 친구 요청 목록을 확인할 수 있습니다.
        상태(pending/accepted/rejected)에 상관없이 모든 요청이 반환됩니다.
        
        반환되는 정보에는 요청 발신자의 상세 정보(이메일, 이름, 프로필 이미지 등)도 포함됩니다.
        """,
        responses={
            200: openapi.Response(
                description="받은 친구 요청 목록",
                schema=FriendRequestSerializer(many=True),
            ),
        },
    )
    @action(detail=False, methods=["get"])
    def received(self, request):
        """List received friend requests."""
        friend_requests = FriendRequest.objects.filter(receiver=request.user)

        page = self.paginate_queryset(friend_requests)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(friend_requests, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        method="get",
        operation_description="""
        현재 사용자가 보낸 모든 친구 요청을 조회합니다.
        
        이 API를 통해 현재 사용자가 다른 사용자에게 보낸 모든 친구 요청 목록을 확인할 수 있습니다.
        상태(pending/accepted/rejected)에 상관없이 모든 요청이 반환됩니다.
        
        반환되는 정보에는 요청 수신자의 상세 정보(이메일, 이름, 프로필 이미지 등)도 포함됩니다.
        """,
        responses={
            200: openapi.Response(
                description="보낸 친구 요청 목록",
                schema=FriendRequestSerializer(many=True),
            ),
        },
    )
    @action(detail=False, methods=["get"])
    def sent(self, request):
        """List sent friend requests."""
        friend_requests = FriendRequest.objects.filter(sender=request.user)

        page = self.paginate_queryset(friend_requests)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(friend_requests, many=True)
        return Response(serializer.data)


class DecoratedTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_description="""
        사용자의 아이디와 비밀번호를 입력받아 JWT Access Token과 Refresh Token을 발급합니다.

        - **Access Token**: API 요청 시 인증에 사용합니다. 만료 시간이 짧습니다.
        - **Refresh Token**: Access Token이 만료되었을 때 새로운 Access Token을 발급받는 데 사용합니다.

        로그인에 성공하면 두 토큰을 모두 반환합니다.
        """,
        responses={
            status.HTTP_200_OK: TokenObtainPairResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: "Invalid credentials",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DecoratedTokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        operation_description="""
        Refresh Token을 입력받아 새로운 JWT Access Token을 발급합니다.

        - **Refresh Token**이 유효할 경우, 새로운 Access Token을 반환합니다.
        - 기존의 Refresh Token은 그대로 사용 가능합니다.
        - Access Token이 만료되었을 때, 로그아웃 없이 인증 상태를 유지할 수 있습니다.
        """,
        responses={
            status.HTTP_200_OK: TokenRefreshResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: "Invalid or expired token",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    """Logout view that blacklists the refresh token"""

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class CreditUsageListView(generics.ListAPIView):
    """
    사용자의 크레딧 사용 내역을 조회하는 API

    사용자의 크레딧 충전 및 사용 내역을 최신순으로 보여줍니다.
    """

    serializer_class = CreditUsageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """사용자의 크레딧 사용 내역 반환"""
        return CreditUsage.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )

    @swagger_auto_schema(
        operation_description="사용자의 크레딧 사용 내역을 최신순으로 반환합니다.",
        responses={
            200: openapi.Response(
                description="크레딧 사용 내역 목록",
                schema=CreditUsageSerializer(many=True),
            ),
            401: "인증되지 않은 사용자",
        },
        tags=["크레딧 관리"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CreditInfoView(APIView):
    """
    사용자의 현재 크레딧 정보를 조회하는 API
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="사용자의 현재 크레딧 정보를 반환합니다.",
        responses={
            200: openapi.Response(
                description="크레딧 정보",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "credits": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="현재 보유한 크레딧 수",
                        )
                    },
                ),
                examples={"application/json": {"credits": 10}},
            ),
            401: "인증되지 않은 사용자",
        },
        tags=["크레딧 관리"],
    )
    def get(self, request):
        """사용자의 현재 크레딧 정보 반환"""
        return Response({"credits": request.user.credits})


class CreditChargeView(APIView):
    """
    크레딧 충전 API

    사용자가 크레딧을 충전할 수 있는 API입니다.
    실제 결제 처리는 구현되어 있지 않으며, 테스트 목적으로 즉시 크레딧이 추가됩니다.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="크레딧을 충전합니다. 실제 결제 처리는 구현되어 있지 않으며, 테스트 목적으로 즉시 크레딧이 추가됩니다.",
        request_body=CreditChargeSerializer,
        responses={
            200: openapi.Response(
                description="충전 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING, description="결과 메시지"
                        ),
                        "amount": openapi.Schema(
                            type=openapi.TYPE_INTEGER, description="충전된 크레딧 수"
                        ),
                        "total_credits": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="충전 후 총 크레딧 수",
                        ),
                    },
                ),
                examples={
                    "application/json": {
                        "message": "크레딧이 성공적으로 충전되었습니다.",
                        "amount": 10,
                        "total_credits": 20,
                    }
                },
            ),
            400: "잘못된 요청",
            401: "인증되지 않은 사용자",
        },
        tags=["크레딧 관리"],
    )
    def post(self, request):
        """크레딧 충전 처리"""
        serializer = CreditChargeSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            result = serializer.save()

            return Response(
                {
                    "message": "크레딧이 성공적으로 충전되었습니다.",
                    "amount": result["amount"],
                    "total_credits": request.user.credits,
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
