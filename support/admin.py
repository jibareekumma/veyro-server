

from django.contrib import admin

from .models import Ticket, TicketReply


class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    extra = 1
    fields = ('message', 'author', 'is_staff_reply', 'created_at')
    readonly_fields = ('author', 'is_staff_reply', 'created_at')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'user', 'subject', 'category', 'status', 'updated_at')
    list_filter = ('status', 'category')
    search_fields = ('ticket_id', 'subject', 'tracking_id', 'user__email')
    readonly_fields = ('ticket_id', 'user', 'created_at', 'updated_at')
    inlines = [TicketReplyInline]

    def has_add_permission(self, request):
        return False

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for obj in instances:
            if isinstance(obj, TicketReply) and obj.pk is None:
                obj.author = request.user
                obj.is_staff_reply = True
            obj.save()
        formset.save_m2m()