from django.urls import path

from . import views

app_name = "resumes"

urlpatterns = [
    path("ping/", views.ping, name="ping"),  # placeholder - replace with real endpoints
]
