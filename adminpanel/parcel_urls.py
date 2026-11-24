

from django.urls import path

from .parcel_views import ParcelDetailView, ParcelEventCreateView, ParcelEventDetailView

urlpatterns = [
    path('parcels/<str:tracking_id>/', ParcelDetailView.as_view()),
    path('parcels/<str:tracking_id>/events/', ParcelEventCreateView.as_view()),
    path('parcels/<str:tracking_id>/events/<int:event_id>/', ParcelEventDetailView.as_view()),
]