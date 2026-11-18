

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import Notification

from .models import Ticket
from .pagination import TicketPagination
from .serializers import TicketDetailSerializer, TicketSerializer

STATUS_KEYS = [key for key, label in Ticket.STATUS_CHOICES]
CATEGORY_KEYS = [key for key, label in Ticket.CATEGORY_CHOICES]


class TicketListCreateView(ListCreateAPIView):
    serializer_class = TicketSerializer
    pagination_class = TicketPagination

    def get_queryset(self):
        queryset = Ticket.objects.filter(user=self.request.user).annotate(
            staff_reply_count=Count('replies', filter=Q(replies__is_staff_reply=True)),
        )

        status_key = self.request.query_params.get('status', '')
        if status_key in STATUS_KEYS:
            queryset = queryset.filter(status=status_key)

        category_key = self.request.query_params.get('category', '')
        if category_key in CATEGORY_KEYS:
            queryset = queryset.filter(category=category_key)

        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(ticket_id__icontains=search)
                | Q(subject__icontains=search)
                | Q(tracking_id__icontains=search)
            )

        return queryset.order_by('-created_at', '-id')

    def perform_create(self, serializer):
        ticket = serializer.save(user=self.request.user)
        Notification.objects.create(
            user=self.request.user,
            kind='system',
            title='Support ticket created',
            message=f'Your ticket {ticket.ticket_id} has been received.',
            tracking_id=ticket.tracking_id,
        )


class TicketDetailView(RetrieveAPIView):
    serializer_class = TicketDetailSerializer

    def get_object(self):
        queryset = Ticket.objects.filter(user=self.request.user).prefetch_related('replies')
        return get_object_or_404(
            queryset,
            ticket_id=self.kwargs['ticket_id'].strip().upper(),
        )


class TicketStatsView(APIView):
    def get(self, request):
        queryset = Ticket.objects.filter(user=request.user)
        counts = queryset.aggregate(
            total=Count('id'),
            open=Count('id', filter=Q(status='open')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            resolved=Count('id', filter=Q(status='resolved')),
            closed=Count('id', filter=Q(status='closed')),
        )
        return Response(counts)