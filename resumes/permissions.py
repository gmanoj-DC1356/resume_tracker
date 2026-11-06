"""Who may do what with resumes.

Rule for now: any active user holding the `view_resume` permission (the "Recruiter" group)
can see every resume. All resource access goes through `can_view_resume`, so tightening the
rule later (per team, per owner) is a change in this one function.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Resume

VIEW_PERMISSION = "resumes.view_resume"
ADD_PERMISSION = "resumes.add_resume"


def can_view_resume(user, resume: Resume) -> bool:
    return bool(user and user.is_active and user.has_perm(VIEW_PERMISSION))


class ResumeCollectionPermission(BasePermission):
    """List needs view_resume; upload needs add_resume. Denied callers get 403."""

    def has_permission(self, request, view) -> bool:
        needed = VIEW_PERMISSION if request.method in SAFE_METHODS else ADD_PERMISSION
        return bool(request.user and request.user.is_active and request.user.has_perm(needed))
