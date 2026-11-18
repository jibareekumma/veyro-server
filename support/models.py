

from django.conf import settings
from django.db import models


class Ticket(models.Model):
    CATEGORY_CHOICES = [
        ('shipments', 'Shipments'),
        ('account', 'Account'),
        ('tracking', 'Tracking'),
        ('billing', 'Billing'),
        ('general', 'General'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_tickets',
    )
    ticket_id = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False)
    subject = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    tracking_id = models.CharField(max_length=20, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.ticket_id:
            self.ticket_id = f'SV-{1000 + self.pk}'
            super().save(update_fields=['ticket_id'])

    def __str__(self):
        return f'{self.ticket_id} - {self.subject}'


class TicketReply(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='replies',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ticket_replies',
    )
    is_staff_reply = models.BooleanField(default=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if not is_new:
            return
        ticket = self.ticket
        fields = ['updated_at']
        if self.is_staff_reply and ticket.status == 'open':
            ticket.status = 'in_progress'
            fields.append('status')
        ticket.save(update_fields=fields)
        if self.is_staff_reply:
            from notifications.models import Notification
            Notification.objects.create(
                user=ticket.user,
                kind='system',
                title='Support replied to your ticket',
                message=f'Our team has responded to ticket {ticket.ticket_id}.',
                tracking_id=ticket.tracking_id,
            )

    def __str__(self):
        return f'{self.ticket.ticket_id} reply'