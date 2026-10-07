

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import GoogleLoginView, LoginView, MeView, RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('google/', GoogleLoginView.as_view()),
    path('me/', MeView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
]