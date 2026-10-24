

from django.urls import path

from .views import ShipmentListCreateView, TrackingView

urlpatterns = [
    path('', ShipmentListCreateView.as_view()),
    path('track/<str:tracking_id>/', TrackingView.as_view()),
]