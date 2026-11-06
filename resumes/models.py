import uuid

from django.conf import settings
from django.db import models


def original_upload_path(instance: "Resume", filename: str) -> str:
    # The stored name is generated here, never taken from the uploaded file name.
    return f"resumes/{instance.id}/original.{instance.file_type}"


def viewable_upload_path(instance: "Resume", filename: str) -> str:
    return f"resumes/{instance.id}/viewable.pdf"


class Resume(models.Model):
    class FileType(models.TextChoices):
        PDF = "pdf"
        DOCX = "docx"

    class Status(models.TextChoices):
        READY = "ready"
        FAILED = "failed"  # e.g. the Word-to-PDF conversion did not work

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate_name = models.CharField(max_length=120)
    original_file = models.FileField(upload_to=original_upload_path)
    # The PDF the reader shows: the original for PDFs, the converted copy for Word files.
    pdf_file = models.FileField(upload_to=viewable_upload_path, blank=True)
    original_filename = models.CharField(max_length=255)  # display only, never used in a path
    file_type = models.CharField(max_length=4, choices=FileType.choices)
    status = models.CharField(max_length=6, choices=Status.choices, default=Status.READY)
    size_bytes = models.PositiveIntegerField()
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return f"{self.candidate_name} ({self.id})"
