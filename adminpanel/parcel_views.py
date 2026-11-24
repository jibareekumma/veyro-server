

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from shipments.models import Shipment

from .alerts import send_shipment_email
from .parcel_serializers import (
    AdminParcelSerializer,
    ParcelEventSerializer,
    ParcelEventUpdateSerializer,
)
from .permissions import CanManageParcels, IsStaffMember

FINAL_STATUSES = ('delivered', 'cancelled')


def normalize(tracking_id):
    return tracking_id.strip().upper()


def read_parcel(tracking_id):
    return get_object_or_404(
        Shipment.objects.select_related('user').prefetch_related('events'),
        tracking_id=normalize(tracking_id),
    )


def lock_parcel(tracking_id):
    return get_object_or_404(
        Shipment.objects.select_related('user').select_for_update(of=('self',)),
        tracking_id=normalize(tracking_id),
    )


def parcel_response(tracking_id, code=status.HTTP_200_OK):
    return Response(AdminParcelSerializer(read_parcel(tracking_id)).data, status=code)


class ParcelDetailView(APIView):
    permission_classes = [IsStaffMember]

    def get(self, request, tracking_id):
        return parcel_response(tracking_id)


class ParcelEventCreateView(APIView):
    permission_classes = [CanManageParcels]

    def post(self, request, tracking_id):
        serializer = ParcelEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            shipment = lock_parcel(tracking_id)

            if shipment.status in FINAL_STATUSES:
                return Response(
                    {'detail': f'This shipment is already {shipment.get_status_display().lower()} and can no longer be updated.'},
                    status=status.HTTP_409_CONFLICT,
                )

            location = data['location'].strip()
            if not location:
                previous = shipment.events.first()
                if previous:
                    location = previous.location

            event = shipment.events.create(
                status=data['status'],
                location=location,
                note=data['note'].strip(),
            )
            shipment.status = data['status']
            shipment.save(update_fields=['status', 'updated_at'])

            transaction.on_commit(lambda: send_shipment_email(shipment, event))

        return parcel_response(tracking_id, status.HTTP_201_CREATED)


class ParcelEventDetailView(APIView):
    permission_classes = [CanManageParcels]

    def patch(self, request, tracking_id, event_id):
        serializer = ParcelEventUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            shipment = lock_parcel(tracking_id)
            event = get_object_or_404(shipment.events, pk=event_id)

            if 'location' in data:
                event.location = data['location'].strip()
            if 'note' in data:
                event.note = data['note'].strip()

            if event.status == 'exception' and not event.note:
                return Response(
                    {'note': 'A problem report needs a description.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            event.save()
            shipment.save(update_fields=['updated_at'])

        return parcel_response(tracking_id)

    def delete(self, request, tracking_id, event_id):
        with transaction.atomic():
            shipment = lock_parcel(tracking_id)
            event = get_object_or_404(shipment.events, pk=event_id)

            if shipment.events.count() <= 1:
                return Response(
                    {'detail': 'The first event of a shipment cannot be removed.'},
                    status=status.HTTP_409_CONFLICT,
                )

            event.delete()
            latest = shipment.events.first()
            shipment.status = latest.status if latest else 'pending'
            shipment.save(update_fields=['status', 'updated_at'])

        return parcel_response(tracking_id)