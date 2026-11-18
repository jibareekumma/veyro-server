
from django.urls import path

from .views import AcceptInviteView, OverviewView, StaffView

urlpatterns = [
    path('overview/', OverviewView.as_view()),
    path('staff/', StaffView.as_view()),
    path('accept-invite/', AcceptInviteView.as_view()),
]