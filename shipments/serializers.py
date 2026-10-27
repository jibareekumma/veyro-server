

from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from .models import Shipment, ShipmentEvent
from .pricing import calculate_pricing, estimated_delivery


class ShipmentSerializer(serializers.ModelSerializer):
    estimated_delivery = serializers.SerializerMethodField()

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
            'estimated_delivery',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'tracking_id',
            'status',
            'base_fee',
            'fuel_surcharge',
            'insurance',
            'total_cost',
            'created_at',
            'updated_at',
        )
        extra_kwargs = {
            'weight': {'min_value': Decimal('0.01')},
            'length': {'min_value': Decimal('0.01')},
            'width': {'min_value': Decimal('0.01')},
            'height': {'min_value': Decimal('0.01')},
        }

    def get_estimated_delivery(self, obj):
        return estimated_delivery(obj)

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
        fields = ('id', 'status', 'location', 'note', 'created_at')


class TrackingSerializer(serializers.ModelSerializer):
    origin_city = serializers.CharField(source='sender_city')
    origin_country = serializers.CharField(source='sender_country')
    destination_city = serializers.CharField(source='receiver_city')
    destination_country = serializers.CharField(source='receiver_country')
    estimated_delivery = serializers.SerializerMethodField()
    current_location = serializers.SerializerMethodField()
    package = serializers.SerializerMethodField()
    events = ShipmentEventSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = (
            'tracking_id',
            'status',
            'origin_city',
            'origin_country',
            'destination_city',
            'destination_country',
            'delivery_method',
            'estimated_delivery',
            'current_location',
            'created_at',
            'updated_at',
            'package',
            'events',
        )

    def get_estimated_delivery(self, obj):
        return estimated_delivery(obj)

    def get_current_location(self, obj):
        if obj.status == 'delivered':
            return obj.receiver_city
        latest_event = obj.events.first()
        if latest_event and latest_event.location:
            return latest_event.location
        return obj.sender_city

    def get_package(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or obj.user_id != request.user.id:
            return None
        return {
            'description': obj.description,
            'category': obj.category,
            'weight': str(obj.weight),
            'length': str(obj.length),
            'width': str(obj.width),
            'height': str(obj.height),
            'fragile': obj.fragile,
        }