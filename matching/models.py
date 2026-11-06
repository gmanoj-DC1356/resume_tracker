from django.db import models

from resumes.models import Resume


class CandidateProfile(models.Model):
    """Structured facts about one resume (role, experience, skills).

    Starter table for the matching module. Today the sample loader fills it; later the resume
    parser fills it. The owner of this app can reshape it before anything depends on it.
    """

    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name="profile")
    role_title = models.CharField(max_length=120)
    years_experience = models.PositiveSmallIntegerField()
    skills = models.JSONField(default=list)  # list of skill names
    summary = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-years_experience", "resume__candidate_name"]

    def __str__(self) -> str:
        return f"{self.resume.candidate_name} - {self.role_title}"
