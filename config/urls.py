

from django.contrib import admin
from django.urls import include, path

from shipments.quotes import QuoteView


urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/', include('accounts.urls')),
    path('api/shipments/', include('shipments.urls')),
    path('api/addresses/', include('addresses.urls')),

    path('api/quotes/', QuoteView.as_view()),
]