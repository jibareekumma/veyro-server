

from django.db.models.signals import post_save
from django.dispatch import receiver

from shipments.models import Shipment, ShipmentEvent

from .services import notify, notify_staff

SELF_EVENT_NOTES = {'Shipment created', 'Shipment details updated'}

STATUS_TITLES = {
    'pending': 'Shipment updated',
    'picked_up': 'Shipment confirmed and picked up',
    'in_transit': 'Shipment in transit',
    'out_for_delivery': 'Shipment out for delivery',
    'delivered': 'Shipment delivered',
    'exception': 'Attention needed on your shipment',
    'cancelled': 'Shipment cancelled',
}


@receiver(post_save, sender=Shipment)
def shipment_created(sender, instance, created, **kwargs):
    if not created:
        return
    notify(
        instance.user,
        'shipment_created',
        'Shipment created',
        f'Shipment {instance.tracking_id} was created and is awaiting confirmation.',
        instance.tracking_id,
    )
    notify_staff(
        'admin_alert',
        'New shipment awaiting confirmation',
        f'{instance.user.full_name} created shipment {instance.tracking_id}.',
        instance.tracking_id,
        exclude_user=instance.user,
    )


@receiver(post_save, sender=ShipmentEvent)
def shipment_event_created(sender, instance, created, **kwargs):
    if not created or instance.note in SELF_EVENT_NOTES:
        return
    shipment = instance.shipment
    message = f'Shipment {shipment.tracking_id} is now {instance.get_status_display()}.'
    if instance.note:
        message = f'{message} {instance.note}'
    notify(
        shipment.user,
        'shipment_update',
        STATUS_TITLES.get(instance.status, 'Shipment updated'),
        message[:255],
        shipment.tracking_id,
    )