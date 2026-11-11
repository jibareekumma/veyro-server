

from rest_framework import serializers

from .models import Address


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = [
            'id',
            'category',
            'address_line',
            'city',
            'state_province',
            'postal_code',
            'country',
            'is_default',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]