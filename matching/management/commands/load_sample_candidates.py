"""Fill CandidateProfile for the synthetic sample resumes (development only).

Run after load_sample_resumes: python manage.py load_sample_candidates
All details are invented. Profiles are keyed by the sample file name.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from matching.models import CandidateProfile
from resumes.models import Resume

DATA_ENGINEER_SKILLS = ["Python", "SQL", "Spark", "Azure", "Airflow", "Delta Lake"]
SOFTWARE_ENGINEER_SKILLS = ["Python", "SQL", "Django", "REST APIs", "Git"]

DATA_ENGINEER = {
    "role_title": "Data Engineer",
    "years_experience": 8,
    "skills": DATA_ENGINEER_SKILLS,
    "summary": "Built Spark batch and streaming pipelines on Azure Databricks for commercial analytics.",
}
SOFTWARE_ENGINEER = {
    "role_title": "Software Engineer",
    "years_experience": 5,
    "skills": SOFTWARE_ENGINEER_SKILLS,
    "summary": "Backend-leaning engineer with experience in REST APIs and automation.",
}

PROFILES_BY_FILENAME = {
    "candidate_a.pdf": DATA_ENGINEER,
    "candidate_a.docx": DATA_ENGINEER,
    "candidate_b.pdf": {
        "role_title": "Analytics Engineer",
        "years_experience": 6,
        "skills": ["Python", "Azure", "SQL", "dbt", "Power BI"],
        "summary": "Analytics engineer focused on trusted reporting datasets and Azure data services.",
    },
    "candidate_c.pdf": SOFTWARE_ENGINEER,
    "candidate_c.docx": SOFTWARE_ENGINEER,
    "candidate_d.pdf": {
        "role_title": "Data Analyst",
        "years_experience": 4,
        "skills": ["SQL", "Azure", "Excel", "Power BI"],
        "summary": "Data analyst experienced in SQL reporting and cloud data basics.",
    },
    "candidate_e_long.pdf": {
        "role_title": "Principal Data Engineer",
        "years_experience": 12,
        "skills": DATA_ENGINEER_SKILLS,
        "summary": "Long-form sample resume used to test multi-page viewing.",
    },
}


class Command(BaseCommand):
    help = "Create sample candidate profiles for the loaded sample resumes (development only)."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Sample data can only be loaded when DJANGO_DEBUG is true.")
        resumes = Resume.objects.filter(original_filename__in=PROFILES_BY_FILENAME)
        if not resumes.exists():
            raise CommandError("No sample resumes found. Run load_sample_resumes first.")
        for resume in resumes:
            _, created = CandidateProfile.objects.update_or_create(
                resume=resume, defaults=PROFILES_BY_FILENAME[resume.original_filename]
            )
            self.stdout.write(f"{'created' if created else 'updated'}: {resume.candidate_name}")
