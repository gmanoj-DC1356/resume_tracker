"""Module 3 - Resume matching engine & knowledge base.

Owner: Vinay (Phase 1)
Starter endpoint so the UI can list candidates. Same access rule as the resumes API: login plus
the Recruiter `view_resume` permission (403 otherwise).
"""
from rest_framework.generics import ListAPIView
from rest_framework.permissions import BasePermission

from resumes.models import Resume
from resumes.permissions import VIEW_PERMISSION

from .models import CandidateProfile
from .serializers import CandidateSerializer


class CanViewCandidates(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_active and request.user.has_perm(VIEW_PERMISSION))


class CandidateListView(ListAPIView):
    """GET /matching/candidates/ lists candidates whose resume is ready to open."""

    serializer_class = CandidateSerializer
    permission_classes = [*ListAPIView.permission_classes, CanViewCandidates]

    def get_queryset(self):
        return CandidateProfile.objects.filter(resume__status=Resume.Status.READY).select_related("resume")
