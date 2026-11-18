

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import signing
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import UserSerializer
from accounts.views import build_tokens

from .permissions import IsStaffMember, IsSuperAdmin
from .serializers import AcceptInviteSerializer, InviteStaffSerializer, StaffSerializer

User = get_user_model()

INVITE_SALT = 'veyro-staff-invite'
INVITE_MAX_AGE = 60 * 60 * 24 * 7


class OverviewView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request):
        week_ago = timezone.now() - timedelta(days=7)
        customers = User.objects.filter(role=User.CUSTOMER)
        staff = User.objects.exclude(role=User.CUSTOMER)
        return Response({
            'total_customers': customers.count(),
            'new_customers_7d': customers.filter(date_joined__gte=week_ago).count(),
            'total_staff': staff.count(),
            'active_staff': staff.filter(is_active=True).count(),
        })


class StaffView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        staff = User.objects.exclude(role=User.CUSTOMER).order_by('-date_joined')
        return Response(StaffSerializer(staff, many=True).data)

    def post(self, request):
        serializer = InviteStaffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.filter(email__iexact=data['email']).first()
        if user is None:
            user = User.objects.create_user(
                email=data['email'],
                password=None,
                full_name=data['full_name'],
                role=data['role'],
            )
        elif user.is_staff_member and not user.has_usable_password():
            user.full_name = data['full_name']
            user.role = data['role']
            user.save(update_fields=['full_name', 'role'])
        else:
            return Response(
                {'email': 'An account with this email already exists.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token = signing.dumps({'uid': user.id}, salt=INVITE_SALT)
        return Response(
            {'user': StaffSerializer(user).data, 'invite_token': token},
            status=status.HTTP_201_CREATED,
        )


class AcceptInviteView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = AcceptInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = signing.loads(
                serializer.validated_data['token'],
                salt=INVITE_SALT,
                max_age=INVITE_MAX_AGE,
            )
        except signing.BadSignature:
            return Response(
                {'detail': 'This invite link is invalid or has expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.filter(id=payload.get('uid')).first()
        if user is None or not user.is_active or not user.is_staff_member or user.has_usable_password():
            return Response(
                {'detail': 'This invite link is no longer valid.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data['password'])
        user.save(update_fields=['password'])
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': build_tokens(user),
        })