"""Load the synthetic sample resumes for local demos: python manage.py load_sample_resumes --username <you>"""
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import APIException

from resumes.models import Resume
from resumes.services import create_resume
from resumes.validators import EXTENSION_TO_TYPE, detect_resume_type


def candidate_name_from(path: Path, file_type: str) -> str:
    name = path.stem.replace("_", " ").title()
    return f"{name} (Word)" if file_type == Resume.FileType.DOCX else name


class Command(BaseCommand):
    help = "Load synthetic sample resumes (development only)."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True, help="Existing user recorded as the uploader.")
        parser.add_argument("--directory", default=str(settings.BASE_DIR / "sample_resumes"))

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Sample data can only be loaded when DJANGO_DEBUG is true.")
        user = get_user_model().objects.filter(username=options["username"]).first()
        if user is None:
            raise CommandError("That user does not exist. Create it with createsuperuser first.")
        directory = Path(options["directory"])
        if not directory.is_dir():
            raise CommandError("Sample directory not found.")

        for path in sorted(directory.iterdir()):
            if path.suffix.lower() in EXTENSION_TO_TYPE:
                self._load_one(path, user)

    def _load_one(self, path: Path, user) -> None:
        if Resume.objects.filter(original_filename=path.name).exists():
            self.stdout.write(f"skipped (already loaded): {path.name}")
            return
        upload = SimpleUploadedFile(path.name, path.read_bytes())
        try:
            file_type = detect_resume_type(upload)
        except APIException as error:
            self.stderr.write(f"rejected {path.name}: {error.detail}")
            return
        resume = create_resume(
            user=user,
            candidate_name=candidate_name_from(path, file_type),
            upload=upload,
            file_type=file_type,
        )
        self.stdout.write(f"loaded {path.name} -> {resume.id} ({resume.status})")
