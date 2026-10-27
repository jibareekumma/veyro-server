from django.urls import path

from .views import ShipmentListCreateView, ShipmentStatsView, TrackingView

urlpatterns = [
    path('', ShipmentListCreateView.as_view()),
    path('stats/', ShipmentStatsView.as_view()),
    path('track/<str:tracking_id>/', TrackingView.as_view()),
]