

from django.shortcuts import get_object_or_404
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Shipment
from .serializers import ShipmentSerializer, TrackingSerializer


class ShipmentListCreateView(ListCreateAPIView):
    serializer_class = ShipmentSerializer

    def get_queryset(self):
        return Shipment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TrackingView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, tracking_id):
        shipment = get_object_or_404(
            Shipment.objects.prefetch_related('events'),
            tracking_id=tracking_id.strip().upper(),
        )
        return Response(TrackingSerializer(shipment).data)