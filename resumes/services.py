import os

from django.core.files.base import ContentFile

from .converter import ConversionError, convert_docx_to_pdf
from .models import Resume

MAX_FILENAME_LENGTH = 255


def create_resume(*, user, candidate_name: str, upload, file_type: str) -> Resume:
    """Store an already-validated upload. Word files are converted to a viewable PDF.

    Files go through Django's storage API only, so the storage backend can change later.
    """
    resume = Resume(
        candidate_name=candidate_name,
        original_filename=os.path.basename(upload.name)[:MAX_FILENAME_LENGTH],
        file_type=file_type,
        size_bytes=upload.size,
        uploaded_by=user,
    )
    resume.original_file.save(upload.name, upload, save=False)
    try:
        _attach_viewable_pdf(resume)
        resume.save()
    except Exception:
        # Do not leave orphaned personal data behind if saving fails.
        resume.original_file.delete(save=False)
        resume.pdf_file.delete(save=False)
        raise
    return resume


def _attach_viewable_pdf(resume: Resume) -> None:
    if resume.file_type == Resume.FileType.PDF:
        resume.pdf_file.name = resume.original_file.name  # same file, no copy
        return
    with resume.original_file.open("rb") as handle:
        docx_bytes = handle.read()
    try:
        pdf_bytes = convert_docx_to_pdf(docx_bytes)
    except ConversionError:
        resume.status = Resume.Status.FAILED
        return
    resume.pdf_file.save("viewable.pdf", ContentFile(pdf_bytes), save=False)
