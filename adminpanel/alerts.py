

from django.conf import settings
from django.core.mail import send_mail

STATUS_LABELS = {
    'pending': 'Pending',
    'picked_up': 'Picked Up',
    'in_transit': 'In Transit',
    'out_for_delivery': 'Out for Delivery',
    'delivered': 'Delivered',
    'exception': 'Delayed',
    'cancelled': 'Cancelled',
}

EMAIL_STATUSES = ('exception', 'delivered')


def recipients_for(shipment):
    emails = []
    for address in (shipment.user.email, shipment.receiver_email):
        cleaned = (address or '').strip().lower()
        if cleaned and cleaned not in emails:
            emails.append(cleaned)
    return emails


def build_message(shipment, event):
    label = STATUS_LABELS.get(event.status, event.status)

    if event.status == 'exception':
        subject = f'Delay reported on shipment {shipment.tracking_id}'
        headline = 'There is a delay with your shipment.'
    elif event.status == 'delivered':
        subject = f'Shipment {shipment.tracking_id} has been delivered'
        headline = 'Your shipment has been delivered.'
    else:
        subject = f'Shipment {shipment.tracking_id} is now {label}'
        headline = f'Your shipment status is now {label}.'

    lines = [
        headline,
        '',
        f'Tracking ID: {shipment.tracking_id}',
        f'Status: {label}',
    ]
    if event.location:
        lines.append(f'Location: {event.location}')
    if event.note:
        lines.append(f'Details: {event.note}')
    lines.append('')
    lines.append(f'Track your shipment: {settings.FRONTEND_URL}/tracking/{shipment.tracking_id}')
    lines.append('')
    lines.append('VEYRO Logistics')

    return subject, '\n'.join(lines)


def send_shipment_email(shipment, event):
    if event.status not in EMAIL_STATUSES:
        return
    emails = recipients_for(shipment)
    if not emails:
        return
    subject, body = build_message(shipment, event)
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        emails,
        fail_silently=True,
    )