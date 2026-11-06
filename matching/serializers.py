from rest_framework import serializers

from .models import CandidateProfile


class CandidateSerializer(serializers.ModelSerializer):
    """A candidate card: the resume to open plus the facts shown on the card."""

    resume_id = serializers.UUIDField(source="resume.id", read_only=True)
    name = serializers.CharField(source="resume.candidate_name", read_only=True)

    class Meta:
        model = CandidateProfile
        fields = ["resume_id", "name", "role_title", "years_experience", "skills", "summary"]
        read_only_fields = fields
