from django.urls import path

from . import views

app_name = "matching"

urlpatterns = [
    path("candidates/", views.CandidateListView.as_view(), name="candidates"),
]
