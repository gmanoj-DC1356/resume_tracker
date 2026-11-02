from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("common.urls")),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/screening/", include("screening.urls")),
    path("api/v1/matching/", include("matching.urls")),
    path("api/v1/vectorsearch/", include("vectorsearch.urls")),
    path("api/v1/resumes/", include("resumes.urls")),
    path("api/v1/interview/", include("interview.urls")),
]
