

from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):

    def get(self, request):
        queryset = Notification.objects.filter(user=request.user)
        unread_count = queryset.filter(is_read=False).count()
        items = queryset[:50]
        return Response({
            'unread_count': unread_count,
            'results': NotificationSerializer(items, many=True).data,
        })


class NotificationReadView(APIView):

    def post(self, request, pk):
        updated = Notification.objects.filter(user=request.user, pk=pk).update(is_read=True)
        if not updated:
            raise Http404
        return Response({'id': pk, 'is_read': True})


class NotificationReadAllView(APIView):

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'unread_count': 0})