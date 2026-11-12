

from django.contrib.auth import get_user_model

from .models import Notification


def notify(user, kind, title, message, tracking_id=''):
    return Notification.objects.create(
        user=user,
        kind=kind,
        title=title,
        message=message,
        tracking_id=tracking_id,
    )


def notify_staff(kind, title, message, tracking_id='', exclude_user=None):
    User = get_user_model()
    staff = User.objects.filter(is_staff=True, is_active=True)
    if exclude_user is not None:
        staff = staff.exclude(pk=exclude_user.pk)
    Notification.objects.bulk_create([
        Notification(
            user=member,
            kind=kind,
            title=title,
            message=message,
            tracking_id=tracking_id,
        )
        for member in staff
    ])