from django.urls import path

from . import views

app_name = "matching"

urlpatterns = [
    path("ping/", views.ping, name="ping"),  # placeholder - replace with real endpoints
]
