

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
        pricing = calculate_pricing(
            validated_data['delivery_method'],
            weight=validated_data['weight'],
            length=validated_data['length'],
            width=validated_data['width'],
            height=validated_data['height'],
            packages=1,
        )
        with transaction.atomic():
            shipment = Shipment.objects.create(**validated_data, **pricing)
            ShipmentEvent.objects.create(
                shipment=shipment,
                status=shipment.status,
                location=shipment.sender_city,
                note='Shipment created',
            )
        return shipment

    def update(self, instance, validated_data):
        pricing = calculate_pricing(
            validated_data.get('delivery_method', instance.delivery_method),
            weight=validated_data.get('weight', instance.weight),
            length=validated_data.get('length', instance.length),
            width=validated_data.get('width', instance.width),
            height=validated_data.get('height', instance.height),
            packages=1,
        )
        with transaction.atomic():
            for field, value in {**validated_data, **pricing}.items():
                setattr(instance, field, value)
            instance.save()
            ShipmentEvent.objects.create(
                shipment=instance,
                status=instance.status,
                location=instance.sender_city,
                note='Shipment details updated',
            )
        return instance


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
    billing = serializers.SerializerMethodField()
    can_modify = serializers.SerializerMethodField()
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
            'billing',
            'can_modify',
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

    def is_owner(self, obj):
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and obj.user_id == request.user.id)

    def get_package(self, obj):
        if not self.is_owner(obj):
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

    def get_billing(self, obj):
        if not self.is_owner(obj):
            return None
        return {
            'base_fee': obj.base_fee,
            'fuel_surcharge': obj.fuel_surcharge,
            'insurance': obj.insurance,
            'total_cost': obj.total_cost,
        }

    def get_can_modify(self, obj):
        return self.is_owner(obj) and obj.status == 'pending' 