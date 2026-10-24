

import secrets

from django.conf import settings
from django.db import models

TRACKING_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def random_block(length):
    return ''.join(secrets.choice(TRACKING_ALPHABET) for _ in range(length))


def generate_tracking_id():
    return f'VY-{random_block(4)}-{random_block(4)}'


class Shipment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('exception', 'Exception'),
        ('cancelled', 'Cancelled'),
    ]

    DELIVERY_CHOICES = [
        ('standard', 'Standard Delivery'),
        ('express', 'Express Delivery'),
        ('priority', 'Priority Delivery'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shipments',
    )
    tracking_id = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    description = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    weight = models.DecimalField(max_digits=8, decimal_places=2)
    length = models.DecimalField(max_digits=8, decimal_places=2)
    width = models.DecimalField(max_digits=8, decimal_places=2)
    height = models.DecimalField(max_digits=8, decimal_places=2)
    fragile = models.BooleanField(default=True)

    sender_full_name = models.CharField(max_length=150)
    sender_phone = models.CharField(max_length=30)
    sender_email = models.EmailField(blank=True)
    sender_address = models.CharField(max_length=255)
    sender_city = models.CharField(max_length=100)
    sender_country = models.CharField(max_length=100)

    receiver_full_name = models.CharField(max_length=150)
    receiver_phone = models.CharField(max_length=30)
    receiver_email = models.EmailField(blank=True)
    receiver_address = models.CharField(max_length=255)
    receiver_city = models.CharField(max_length=100)
    receiver_country = models.CharField(max_length=100)

    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES)

    base_fee = models.PositiveIntegerField()
    fuel_surcharge = models.PositiveIntegerField()
    insurance = models.PositiveIntegerField()
    total_cost = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.tracking_id:
            for _ in range(10):
                candidate = generate_tracking_id()
                if not Shipment.objects.filter(tracking_id=candidate).exists():
                    self.tracking_id = candidate
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.tracking_id


class ShipmentEvent(models.Model):
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='events',
    )
    status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES)
    location = models.CharField(max_length=150, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.shipment.tracking_id} - {self.status}'