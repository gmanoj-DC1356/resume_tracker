from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.common.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/screening/", include("apps.screening.urls")),
    path("api/v1/matching/", include("apps.matching.urls")),
    path("api/v1/vectorsearch/", include("apps.vectorsearch.urls")),
    path("api/v1/resumes/", include("apps.resumes.urls")),
    path("api/v1/interview/", include("apps.interview.urls")),
]
