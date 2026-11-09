

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()

MAX_AVATAR_SIZE = 2 * 1024 * 1024
ALLOWED_AVATAR_TYPES = ('image/jpeg', 'image/png', 'image/webp', 'image/gif')


def detect_image_type(header):
    if header.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if header.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
        return 'image/gif'
    if header[0:4] == b'RIFF' and header[8:12] == b'WEBP':
        return 'image/webp'
    return None


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'phone', 'country', 'avatar')

    def get_avatar(self, obj):
        if not obj.avatar_data:
            return None
        stamp = int(obj.avatar_updated.timestamp()) if obj.avatar_updated else 0
        path = f'/api/auth/avatar/{obj.id}/?v={stamp}'
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(path)
        return path


class AvatarUploadSerializer(serializers.Serializer):
    avatar = serializers.FileField()

    def validate_avatar(self, value):
        if value.size > MAX_AVATAR_SIZE:
            raise serializers.ValidationError('Image must be 2MB or smaller.')
        header = value.read(16)
        value.seek(0)
        detected = detect_image_type(header)
        if detected is None or detected not in ALLOWED_AVATAR_TYPES:
            raise serializers.ValidationError('Upload a JPG, PNG, WEBP or GIF image.')
        value.detected_type = detected
        return value


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('full_name', 'email', 'phone', 'country', 'password', 'confirm_password')
        extra_kwargs = {
            'full_name': {'required': True, 'allow_blank': False},
            'phone': {'required': True, 'allow_blank': False},
            'country': {'required': True, 'allow_blank': False},
        }

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as error:
            raise serializers.ValidationError({'password': list(error.messages)})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        return User.objects.create_user(password=password, **validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class GoogleLoginSerializer(serializers.Serializer):
    credential = serializers.CharField()