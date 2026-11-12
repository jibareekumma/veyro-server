

from django.conf import settings
from django.db import models


class Notification(models.Model):
    KIND_CHOICES = [
        ('shipment_created', 'Shipment created'),
        ('shipment_update', 'Shipment update'),
        ('admin_alert', 'Admin alert'),
        ('payment', 'Payment'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    kind = models.CharField(max_length=30, choices=KIND_CHOICES, default='system')
    title = models.CharField(max_length=150)
    message = models.CharField(max_length=255)
    tracking_id = models.CharField(max_length=20, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.title}'