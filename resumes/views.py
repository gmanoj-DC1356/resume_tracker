"""Module 5 - Resume viewer: upload, list, details and secure file serving.

Owner: Manoj (Phase 1)
Every endpoint requires login (project default). Access to a specific resume goes through
`can_view_resume`; callers who may not see it get the same 404 as a missing resume.
"""
from uuid import UUID

from django.conf import settings
from django.http import FileResponse
from django.utils.cache import patch_cache_control
from rest_framework.exceptions import NotFound
from rest_framework.negotiation import BaseContentNegotiation
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import PayloadTooLarge, UnreadableResume
from .models import Resume
from .permissions import ResumeCollectionPermission, can_view_resume
from .serializers import ResumeSerializer, ResumeUploadSerializer
from .services import create_resume

PDF_CONTENT_TYPE = "application/pdf"
# Allowance for multipart boundaries and the name field on top of the file itself.
MULTIPART_OVERHEAD_BYTES = 64 * 1024


def get_viewable_resume(user, pk: UUID) -> Resume:
    resume = Resume.objects.filter(pk=pk).first()
    if resume is None or not can_view_resume(user, resume):
        raise NotFound()
    return resume


def reject_oversized_request(request) -> None:
    """Refuse obviously huge uploads from the Content-Length header, before parsing the body."""
    declared = request.META.get("CONTENT_LENGTH", "")
    if declared.isdigit() and int(declared) > settings.RESUME_MAX_UPLOAD_BYTES + MULTIPART_OVERHEAD_BYTES:
        raise PayloadTooLarge()


class ResumeCollectionView(APIView):
    """GET /resumes/ lists resumes; POST /resumes/ uploads one (multipart form)."""

    parser_classes = [MultiPartParser]
    permission_classes = [*APIView.permission_classes, ResumeCollectionPermission]

    def get(self, request):
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(Resume.objects.all(), request, view=self)
        return paginator.get_paginated_response(ResumeSerializer(page, many=True).data)

    def post(self, request):
        reject_oversized_request(request)
        serializer = ResumeUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resume = create_resume(
            user=request.user,
            candidate_name=serializer.validated_data["candidate_name"],
            upload=serializer.validated_data["file"],
            file_type=serializer.validated_data["file_type"],
        )
        return Response(ResumeSerializer(resume).data, status=201)


class ResumeDetailView(APIView):
    """GET /resumes/{id}/ returns the resume's details (no file)."""

    def get(self, request, pk: UUID):
        return Response(ResumeSerializer(get_viewable_resume(request.user, pk)).data)


class PdfContentNegotiation(BaseContentNegotiation):
    """The file endpoint always answers with the PDF, whatever the client's Accept header says."""

    def select_parser(self, request, parsers):
        return parsers[0]

    def select_renderer(self, request, renderers, format_suffix=None):
        return renderers[0], renderers[0].media_type


class ResumeFileView(APIView):
    """GET /resumes/{id}/file/ streams the viewable PDF after the access check."""

    content_negotiation_class = PdfContentNegotiation

    def get(self, request, pk: UUID):
        resume = get_viewable_resume(request.user, pk)
        if resume.status != Resume.Status.READY or not resume.pdf_file:
            raise UnreadableResume()
        try:
            handle = resume.pdf_file.open("rb")
        except OSError as error:
            raise UnreadableResume() from error
        # Inline display; the name sent to the browser is the resume id, never the uploaded name.
        response = FileResponse(handle, content_type=PDF_CONTENT_TYPE, filename=f"{resume.id}.pdf")
        response["X-Content-Type-Options"] = "nosniff"
        patch_cache_control(response, private=True, no_store=True)
        return response
