

from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from .models import Shipment, ShipmentEvent
from .pricing import calculate_pricing


class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = (
            'tracking_id',
            'status',
            'description',
            'category',
            'weight',
            'length',
            'width',
            'height',
            'fragile',
            'sender_full_name',
            'sender_phone',
            'sender_email',
            'sender_address',
            'sender_city',
            'sender_country',
            'receiver_full_name',
            'receiver_phone',
            'receiver_email',
            'receiver_address',
            'receiver_city',
            'receiver_country',
            'delivery_method',
            'base_fee',
            'fuel_surcharge',
            'insurance',
            'total_cost',
            'created_at',
        )
        read_only_fields = (
            'tracking_id',
            'status',
            'base_fee',
            'fuel_surcharge',
            'insurance',
            'total_cost',
            'created_at',
        )
        extra_kwargs = {
            'weight': {'min_value': Decimal('0.01')},
            'length': {'min_value': Decimal('0.01')},
            'width': {'min_value': Decimal('0.01')},
            'height': {'min_value': Decimal('0.01')},
        }

    def create(self, validated_data):
        pricing = calculate_pricing(validated_data['delivery_method'])
        with transaction.atomic():
            shipment = Shipment.objects.create(**validated_data, **pricing)
            ShipmentEvent.objects.create(
                shipment=shipment,
                status=shipment.status,
                location=shipment.sender_city,
                note='Shipment created',
            )
        return shipment


class ShipmentEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentEvent
        fields = ('status', 'location', 'note', 'created_at')


class TrackingSerializer(serializers.ModelSerializer):
    origin_city = serializers.CharField(source='sender_city')
    destination_city = serializers.CharField(source='receiver_city')
    events = ShipmentEventSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = (
            'tracking_id',
            'status',
            'origin_city',
            'destination_city',
            'delivery_method',
            'created_at',
            'events',
        )