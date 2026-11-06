from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Resume

RECRUITER_GROUP = "Recruiter"
RECRUITER_PERMISSIONS = ("view_resume", "add_resume")


def ensure_recruiter_group(sender, **kwargs) -> None:
    """After migrate: make sure the Recruiter group exists with the resume permissions."""
    group, _ = Group.objects.get_or_create(name=RECRUITER_GROUP)
    permissions = Permission.objects.filter(
        content_type__app_label="resumes", codename__in=RECRUITER_PERMISSIONS
    )
    group.permissions.add(*permissions)


@receiver(post_delete, sender=Resume)
def delete_resume_files(sender, instance: Resume, **kwargs) -> None:
    """Remove stored files with the record so no personal data is left behind."""
    instance.original_file.delete(save=False)
    if instance.pdf_file and instance.pdf_file.name != instance.original_file.name:
        instance.pdf_file.delete(save=False)
