

from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

DELIVERY_PRICES = {
    'standard': 1250,
    'express': 1890,
    'priority': 3200,
}

DELIVERY_DAYS = {
    'standard': 10,
    'express': 4,
    'priority': 2,
}

PER_KG_CENTS = {
    'standard': 150,
    'express': 250,
    'priority': 400,
}

MODE_PERCENT = {
    'ocean': 100,
    'road': 115,
    'air': 160,
}

METHOD_PERCENT = {
    'fcl': 100,
    'lcl': 110,
}

INSURANCE_CENTS = 50
FUEL_PERCENT = 16
INCLUDED_KG = Decimal('1')
VOLUMETRIC_DIVISOR = Decimal('5000')


def chargeable_weight(weight, length, width, height, packages=1):
    volumetric = (Decimal(length) * Decimal(width) * Decimal(height) * Decimal(packages)) / VOLUMETRIC_DIVISOR
    return max(Decimal(weight), volumetric)


def calculate_pricing(
    delivery_method,
    weight=None,
    length=None,
    width=None,
    height=None,
    packages=1,
    mode=None,
    method=None,
):
    total = DELIVERY_PRICES[delivery_method]

    if weight is not None:
        billable = chargeable_weight(weight, length, width, height, packages)
        extra_kg = max(Decimal('0'), billable - INCLUDED_KG)
        extra_cents = (extra_kg * PER_KG_CENTS[delivery_method]).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        total += int(extra_cents)

    mode_percent = MODE_PERCENT.get(mode, 100)
    method_percent = METHOD_PERCENT.get(method, 100)
    total = (total * mode_percent * method_percent + 5000) // 10000

    fuel = (total * FUEL_PERCENT + 50) // 100
    base = total - fuel - INSURANCE_CENTS
    return {
        'base_fee': base,
        'fuel_surcharge': fuel,
        'insurance': INSURANCE_CENTS,
        'total_cost': total,
    }


def estimated_delivery(shipment):
    return shipment.created_at.date() + timedelta(days=DELIVERY_DAYS[shipment.delivery_method])