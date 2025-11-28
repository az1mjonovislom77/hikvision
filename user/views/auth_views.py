from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema
from user.serializers.auth_serializers import SignInSerializer, LogoutSerializer, MeSerializer
from user.services.token_service import UserTokenService


@extend_schema(tags=["Auth"])
class SignInAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = SignInSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        tokens = UserTokenService.get_tokens_for_user(user)

        response = Response(
            {
                "success": True,
                "message": "User logged in successfully",
                "data": {"access": tokens["access"]}
            },
            status=status.HTTP_200_OK
        )

        UserTokenService.set_refresh_cookie(response, tokens["refresh"])

        return response


@extend_schema(tags=["Auth"])
class RefreshTokenAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_token = request.COOKIES.get(UserTokenService.COOKIE_NAME)

        if not refresh_token:
            return Response(
                {"detail": "Refresh token not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            access = str(UserTokenService.get_tokens_for_user_from_refresh(refresh_token))
            return Response({"access": access})

        except Exception:
            return Response(
                {"detail": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )


@extend_schema(tags=["Auth"])
class LogOutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response = Response(
            {"detail": "Successfully logged out"},
            status=status.HTTP_204_NO_CONTENT
        )

        UserTokenService.clear_refresh_cookie(response)
        return response


@extend_schema(tags=["Profile"])
class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MeSerializer

    def get(self, request):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)
