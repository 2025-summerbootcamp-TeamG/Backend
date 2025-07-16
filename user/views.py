from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSignupSerializer, EmailTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiTypes

class UserSignupView(generics.CreateAPIView):
    serializer_class = UserSignupSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="회원가입",
        description="새로운 유저를 회원가입 시킴",
        request=UserSignupSerializer,
        responses={
            201: UserSignupSerializer,
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="입력값 오류",
                examples=[
                    OpenApiExample(
                        "EmailExists",
                        value={"email": ["이미 사용중인 이메일입니다."]},
                        status_codes=["400"]
                    ),
                    OpenApiExample(
                        "PasswordMismatch",
                        value={"password2": "비밀번호가 일치하지 않습니다."},
                        status_codes=["400"]
                    )
                ]
            )
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class UserLoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="로그인 (JWT 토큰 발급)",
        description="이메일과 비밀번호로 JWT 토큰(Access, Refresh)을 발급받습니다.",
        request=EmailTokenObtainPairSerializer,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="성공",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "refresh": "<refresh_token>",
                            "access": "<access_token>"
                        },
                        status_codes=["200"]
                    )
                ]
            ),
            401: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="인증 실패",
                examples=[
                    OpenApiExample(
                        "InvalidCredentials",
                        value={"detail": "No active account found with the given credentials"},
                        status_codes=["401"]
                    )
                ]
            )
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="로그아웃 (Refresh 토큰 블랙리스트)",
        description="Refresh 토큰을 블랙리스트 처리하여 로그아웃합니다.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh': {'type': 'string', 'description': 'Refresh 토큰'}
                },
                'required': ['refresh']
            }
        },
        responses={
            205: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="성공",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"message": "로그아웃 완료!"},
                        status_codes=["205"]
                    )
                ]
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="입력값 오류",
                examples=[
                    OpenApiExample(
                        "BadRequest",
                        value={"error": "잘못된 요청입니다."},
                        status_codes=["400"]
                    )
                ]
            )
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "로그아웃 완료!"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "잘못된 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)


