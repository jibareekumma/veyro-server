

from decimal import Decimal

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .pricing import (
    DELIVERY_DAYS,
    DELIVERY_PRICES,
    METHOD_PERCENT,
    MODE_PERCENT,
    calculate_pricing,
    chargeable_weight,
)


class QuoteSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=list(MODE_PERCENT))
    delivery_method = serializers.ChoiceField(choices=list(DELIVERY_PRICES))
    freight_method = serializers.ChoiceField(choices=list(METHOD_PERCENT), default='fcl')
    origin = serializers.CharField(max_length=150)
    destination = serializers.CharField(max_length=150)
    packages = serializers.IntegerField(min_value=1, max_value=1000)
    weight = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal('0.01'))
    length = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal('0.01'))
    width = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal('0.01'))
    height = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal('0.01'))

    def validate(self, attrs):
        if attrs['origin'].strip().lower() == attrs['destination'].strip().lower():
            raise serializers.ValidationError('Origin and destination must be different.')
        return attrs


class QuoteView(APIView):
    def post(self, request):
        serializer = QuoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        pricing = calculate_pricing(
            data['delivery_method'],
            weight=data['weight'],
            length=data['length'],
            width=data['width'],
            height=data['height'],
            packages=data['packages'],
            mode=data['mode'],
            method=data['freight_method'],
        )

        billable = chargeable_weight(
            data['weight'],
            data['length'],
            data['width'],
            data['height'],
            data['packages'],
        )

        return Response({
            **pricing,
            'chargeable_weight': str(billable.quantize(Decimal('0.01'))),
            'estimated_days': DELIVERY_DAYS[data['delivery_method']],
            'origin': data['origin'],
            'destination': data['destination'],
        })