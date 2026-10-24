

from django.contrib import admin

from .models import Shipment, ShipmentEvent


class ShipmentEventInline(admin.TabularInline):
    model = ShipmentEvent
    extra = 0


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        'tracking_id',
        'user',
        'status',
        'sender_city',
        'receiver_city',
        'delivery_method',
        'created_at',
    )
    list_filter = ('status', 'delivery_method')
    search_fields = ('tracking_id', 'user__email', 'sender_full_name', 'receiver_full_name')
    readonly_fields = ('tracking_id', 'created_at', 'updated_at')
    inlines = [ShipmentEventInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change and 'status' in form.changed_data:
            ShipmentEvent.objects.create(
                shipment=obj,
                status=obj.status,
                note=f'Status updated to {obj.get_status_display()}',
            )