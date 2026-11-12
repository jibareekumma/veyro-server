

from django.urls import path

from .views import NotificationListView, NotificationReadAllView, NotificationReadView

urlpatterns = [
    path('', NotificationListView.as_view()),
    path('read-all/', NotificationReadAllView.as_view()),
    path('<int:pk>/read/', NotificationReadView.as_view()),
]