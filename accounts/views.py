
import os

from django.contrib.auth import authenticate, get_user_model
from django.http import Http404, HttpResponse
from django.utils import timezone
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    AvatarUploadSerializer,
    GoogleLoginSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


def build_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'user': UserSerializer(user, context={'request': request}).data, 'tokens': build_tokens(user)},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data['email'].lower(),
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response(
                {'detail': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response({'user': UserSerializer(user, context={'request': request}).data, 'tokens': build_tokens(user)})


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client_id = os.environ.get('GOOGLE_CLIENT_ID')
        if not client_id:
            return Response(
                {'detail': 'Google sign-in is not configured on the server.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        try:
            info = id_token.verify_oauth2_token(
                serializer.validated_data['credential'],
                google_requests.Request(),
                client_id,
                clock_skew_in_seconds=10,
            )
        except ValueError:
            return Response(
                {'detail': 'Invalid Google sign-in. Please try again.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not info.get('email_verified'):
            return Response(
                {'detail': 'Your Google email is not verified.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        email = info['email'].lower()
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            user = User.objects.create_user(
                email=email,
                password=None,
                full_name=info.get('name') or email.split('@')[0],
            )
        if not user.is_active:
            return Response(
                {'detail': 'This account is disabled.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response({'user': UserSerializer(user, context={'request': request}).data, 'tokens': build_tokens(user)})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)


class AvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = AvatarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image = serializer.validated_data['avatar']
        user = request.user
        user.avatar_data = image.read()
        user.avatar_type = image.detected_type
        user.avatar_updated = timezone.now()
        user.save(update_fields=['avatar_data', 'avatar_type', 'avatar_updated'])
        return Response(UserSerializer(user, context={'request': request}).data)

    def delete(self, request):
        user = request.user
        user.avatar_data = None
        user.avatar_type = ''
        user.avatar_updated = None
        user.save(update_fields=['avatar_data', 'avatar_type', 'avatar_updated'])
        return Response(UserSerializer(user, context={'request': request}).data)


class AvatarImageView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, user_id):
        user = User.objects.filter(id=user_id).first()
        if user is None or not user.avatar_data:
            raise Http404
        response = HttpResponse(bytes(user.avatar_data), content_type=user.avatar_type or 'image/jpeg')
        response['Cache-Control'] = 'public, max-age=31536000, immutable'
        return response