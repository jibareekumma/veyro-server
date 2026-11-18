

from rest_framework import serializers

from .models import Ticket, TicketReply


class TicketReplySerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = TicketReply
        fields = ('id', 'message', 'is_staff_reply', 'author_name', 'created_at')

    def get_author_name(self, obj):
        return 'Support Team' if obj.is_staff_reply else 'You'


class TicketSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source='get_category_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    has_response = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = (
            'id',
            'ticket_id',
            'subject',
            'category',
            'category_label',
            'tracking_id',
            'description',
            'status',
            'status_label',
            'has_response',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('ticket_id', 'status', 'created_at', 'updated_at')
        extra_kwargs = {
            'description': {'max_length': 2000},
        }

    def validate_description(self, value):
        if len(value) < 10:
            raise serializers.ValidationError('Please describe the problem in at least 10 characters.')
        return value

    def validate_tracking_id(self, value):
        return value.strip().upper()

    def get_has_response(self, obj):
        count = getattr(obj, 'staff_reply_count', None)
        if count is None:
            return any(reply.is_staff_reply for reply in obj.replies.all())
        return count > 0


class TicketDetailSerializer(TicketSerializer):
    replies = TicketReplySerializer(many=True, read_only=True)

    class Meta(TicketSerializer.Meta):
        fields = TicketSerializer.Meta.fields + ('replies',)