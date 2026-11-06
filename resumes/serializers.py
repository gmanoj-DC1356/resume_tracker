from rest_framework import serializers

from .models import Resume
from .validators import detect_resume_type

MAX_NAME_LENGTH = 120
MAX_UPLOAD_NAME_LENGTH = 255


class ResumeSerializer(serializers.ModelSerializer):
    """Read-only view of a resume. Never exposes storage paths."""

    class Meta:
        model = Resume
        fields = ["id", "candidate_name", "original_filename", "file_type", "status", "size_bytes", "uploaded_at"]
        read_only_fields = fields


class ResumeUploadSerializer(serializers.Serializer):
    candidate_name = serializers.CharField(max_length=MAX_NAME_LENGTH)
    file = serializers.FileField(max_length=MAX_UPLOAD_NAME_LENGTH)

    def validate_candidate_name(self, value: str) -> str:
        if not value.isprintable():
            raise serializers.ValidationError("Name contains invalid characters.")
        return value

    def validate(self, attrs: dict) -> dict:
        # Raises 413 (too large) or 415 (wrong type) before anything is stored.
        attrs["file_type"] = detect_resume_type(attrs["file"])
        return attrs
