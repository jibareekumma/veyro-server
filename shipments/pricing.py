

DELIVERY_PRICES = {
    'standard': 1250,
    'express': 1890,
    'priority': 3200,
}

INSURANCE_CENTS = 50


def calculate_pricing(delivery_method):
    total = DELIVERY_PRICES[delivery_method]
    fuel = (total * 16 + 50) // 100
    base = total - fuel - INSURANCE_CENTS
    return {
        'base_fee': base,
        'fuel_surcharge': fuel,
        'insurance': INSURANCE_CENTS,
        'total_cost': total,
    }