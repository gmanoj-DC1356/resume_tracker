from django.apps import AppConfig
from django.db.models.signals import post_migrate


class ResumesConfig(AppConfig):
    name = "resumes"

    def ready(self) -> None:
        from . import signals

        post_migrate.connect(signals.ensure_recruiter_group, sender=self)
