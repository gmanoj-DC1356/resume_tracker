"""Upload validation. Trust the file's content, never its name or declared content type."""
import zipfile
from pathlib import Path

from django.conf import settings

from .exceptions import PayloadTooLarge, UnsupportedResumeType
from .models import Resume

PDF_SIGNATURE = b"%PDF-"
DOCX_REQUIRED_PART = "word/document.xml"
EXTENSION_TO_TYPE = {
    ".pdf": Resume.FileType.PDF,
    ".docx": Resume.FileType.DOCX,
}


def _looks_like_pdf(upload) -> bool:
    return upload.read(len(PDF_SIGNATURE)) == PDF_SIGNATURE


def _looks_like_docx(upload) -> bool:
    try:
        with zipfile.ZipFile(upload) as archive:
            parts = archive.infolist()
            if sum(part.file_size for part in parts) > settings.RESUME_MAX_UNCOMPRESSED_BYTES:
                return False  # zip-bomb guard
            return DOCX_REQUIRED_PART in {part.filename for part in parts}
    except zipfile.BadZipFile:
        return False


_CONTENT_CHECKS = {
    Resume.FileType.PDF: _looks_like_pdf,
    Resume.FileType.DOCX: _looks_like_docx,
}


def detect_resume_type(upload) -> str:
    """Return the validated file type ('pdf' or 'docx') or raise a 413/415 API error."""
    if upload.size > settings.RESUME_MAX_UPLOAD_BYTES:
        raise PayloadTooLarge()
    file_type = EXTENSION_TO_TYPE.get(Path(upload.name).suffix.lower())
    if file_type is None:
        raise UnsupportedResumeType()
    upload.seek(0)
    matches_content = _CONTENT_CHECKS[file_type](upload)
    upload.seek(0)
    if not matches_content:
        raise UnsupportedResumeType()
    return file_type
