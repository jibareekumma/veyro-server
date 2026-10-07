

import os

from django.contrib.auth import authenticate, get_user_model
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import GoogleLoginSerializer, LoginSerializer, RegisterSerializer, UserSerializer

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
            {'user': UserSerializer(user).data, 'tokens': build_tokens(user)},
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
        return Response({'user': UserSerializer(user).data, 'tokens': build_tokens(user)})


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
        return Response({'user': UserSerializer(user).data, 'tokens': build_tokens(user)})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)