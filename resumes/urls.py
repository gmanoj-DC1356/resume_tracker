from django.urls import path

from . import views

app_name = "resumes"

urlpatterns = [
    path("", views.ResumeCollectionView.as_view(), name="collection"),
    path("<uuid:pk>/", views.ResumeDetailView.as_view(), name="detail"),
    path("<uuid:pk>/file/", views.ResumeFileView.as_view(), name="file"),
]
