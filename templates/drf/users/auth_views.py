"""JWT auth views for the users DRF API."""

from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from users.serializers import RegisterSerializer, UserReadSerializer


class RegisterView(generics.GenericAPIView):
    """Register a new user and return JWT tokens."""

    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request: Request) -> Response:
        """Create the user and return access + refresh tokens."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserReadSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveAPIView):
    """Return the currently authenticated user."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserReadSerializer

    def get_object(self) -> User:
        """Return the request user."""
        return self.request.user
