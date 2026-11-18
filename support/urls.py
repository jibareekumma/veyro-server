

from django.urls import path

from .views import TicketDetailView, TicketListCreateView, TicketStatsView

urlpatterns = [
    path('', TicketListCreateView.as_view()),
    path('stats/', TicketStatsView.as_view()),
    path('<str:ticket_id>/', TicketDetailView.as_view()),
]