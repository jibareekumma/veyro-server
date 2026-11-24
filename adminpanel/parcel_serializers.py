

from rest_framework import serializers

from shipments.models import Shipment
from shipments.serializers import ShipmentEventSerializer


class AdminParcelSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='user.full_name', read_only=True)
    customer_email = serializers.CharField(source='user.email', read_only=True)
    current_location = serializers.SerializerMethodField()
    events = ShipmentEventSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = (
            'tracking_id',
            'status',
            'delivery_method',
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
            'customer_name',
            'customer_email',
            'current_location',
            'created_at',
            'updated_at',
            'events',
        )

    def get_current_location(self, obj):
        if obj.status == 'delivered':
            return obj.receiver_city
        latest_event = obj.events.first()
        if latest_event and latest_event.location:
            return latest_event.location
        return obj.sender_city


class ParcelEventSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Shipment.STATUS_CHOICES)
    location = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    note = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')

    def validate(self, attrs):
        if attrs['status'] == 'exception' and not attrs.get('note', '').strip():
            raise serializers.ValidationError({'note': 'Describe the problem so the customer knows what happened.'})
        return attrs


class ParcelEventUpdateSerializer(serializers.Serializer):
    location = serializers.CharField(max_length=150, required=False, allow_blank=True)
    note = serializers.CharField(max_length=255, required=False, allow_blank=True)