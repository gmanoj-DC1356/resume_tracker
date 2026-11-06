from django.contrib import admin

from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    """Read-only overview. Uploads go through the API so validation and conversion always run."""

    list_display = ("candidate_name", "file_type", "status", "size_bytes", "uploaded_by", "uploaded_at")
    list_filter = ("file_type", "status")
    search_fields = ("candidate_name",)
    exclude = ("original_file", "pdf_file")
    readonly_fields = (
        "id", "candidate_name", "original_filename", "file_type", "status",
        "size_bytes", "uploaded_by", "uploaded_at",
    )

    def has_add_permission(self, request) -> bool:
        return False
