

from django.urls import path

from .views import ShipmentDetailView, ShipmentListCreateView, ShipmentStatsView, TrackingView

urlpatterns = [
    path('', ShipmentListCreateView.as_view()),
    path('stats/', ShipmentStatsView.as_view()),
    path('track/<str:tracking_id>/', TrackingView.as_view()),
    path('<str:tracking_id>/', ShipmentDetailView.as_view()),
]