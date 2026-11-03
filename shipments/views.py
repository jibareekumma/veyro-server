

from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Shipment
from .pagination import ShipmentPagination
from .pricing import estimated_delivery
from .serializers import ShipmentSerializer, TrackingSerializer

STATUS_GROUPS = {
    'active': ['pending', 'picked_up', 'in_transit', 'out_for_delivery', 'exception'],
    'processing': ['pending'],
    'in_transit': ['picked_up', 'in_transit', 'out_for_delivery'],
    'delivered': ['delivered'],
    'attention': ['exception'],
    'cancelled': ['cancelled'],
}


class ShipmentListCreateView(ListCreateAPIView):
    serializer_class = ShipmentSerializer
    pagination_class = ShipmentPagination

    def get_queryset(self):
        queryset = Shipment.objects.filter(user=self.request.user)

        status_key = self.request.query_params.get('status', '')
        if status_key in STATUS_GROUPS:
            queryset = queryset.filter(status__in=STATUS_GROUPS[status_key])

        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(tracking_id__icontains=search)
                | Q(description__icontains=search)
                | Q(sender_city__icontains=search)
                | Q(sender_country__icontains=search)
                | Q(receiver_city__icontains=search)
                | Q(receiver_country__icontains=search)
            )

        if self.request.query_params.get('ordering') == 'oldest':
            return queryset.order_by('created_at', 'id')
        return queryset.order_by('-created_at', '-id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ShipmentDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ShipmentSerializer
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Shipment.objects.filter(user=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        if self.request.method in ('PATCH', 'DELETE'):
            queryset = queryset.select_for_update()
        shipment = get_object_or_404(
            queryset,
            tracking_id=self.kwargs['tracking_id'].strip().upper(),
        )
        self.check_object_permissions(self.request, shipment)
        return shipment

    def locked_response(self):
        return Response(
            {'detail': 'Only shipments that are still processing can be changed.'},
            status=status.HTTP_409_CONFLICT,
        )

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            if self.get_object().status != 'pending':
                return self.locked_response()
            return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            shipment = self.get_object()
            if shipment.status != 'pending':
                return self.locked_response()
            shipment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShipmentStatsView(APIView):
    def get(self, request):
        queryset = Shipment.objects.filter(user=request.user)

        counts = queryset.aggregate(
            active=Count('id', filter=Q(status__in=STATUS_GROUPS['active'])),
            in_transit=Count('id', filter=Q(status__in=STATUS_GROUPS['in_transit'])),
            delivered=Count('id', filter=Q(status__in=STATUS_GROUPS['delivered'])),
            needs_attention=Count('id', filter=Q(status__in=STATUS_GROUPS['attention'])),
        )

        attention = None
        flagged = queryset.filter(status='exception').order_by ('-updated_at').first()
        if flagged:
            latest_event = flagged.events.first()
            attention = {
                'tracking_id': flagged.tracking_id,
                'location': latest_event.location if latest_event and latest_event.location else flagged.sender_city,
                'estimated_delivery': estimated_delivery(flagged),
            }

        counts['attention'] = attention
        return Response(counts)


class TrackingView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, tracking_id):
        shipment = get_object_or_404(
            Shipment.objects.prefetch_related('events'),
            tracking_id=tracking_id.strip().upper(),
        )
        return Response(TrackingSerializer(shipment, context={'request': request}).data)