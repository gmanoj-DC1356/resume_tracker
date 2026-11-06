"""Word (.docx) to PDF conversion with headless LibreOffice.

Security notes: the command is a fixed argument list (no shell), the input name is a constant we
choose, it runs in throw-away temp folders with its own profile, and it has a hard timeout.
Only the exception type is logged, never file names or tool output.
"""
import logging
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

INPUT_NAME = "input.docx"
OUTPUT_NAME = "input.pdf"
PDF_SIGNATURE = b"%PDF-"


class ConversionError(Exception):
    """The Word file could not be converted to PDF."""


def convert_docx_to_pdf(docx_bytes: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as work_dir, tempfile.TemporaryDirectory() as profile_dir:
        work = Path(work_dir)
        source = work / INPUT_NAME
        source.write_bytes(docx_bytes)
        command = [
            settings.LIBREOFFICE_BIN,
            "--headless",
            "--norestore",
            "--nolockcheck",
            f"-env:UserInstallation={Path(profile_dir).as_uri()}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(work),
            str(source),
        ]
        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=settings.RESUME_CONVERSION_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.SubprocessError) as error:
            logger.warning("Word to PDF conversion failed: %s", type(error).__name__)
            raise ConversionError from error
        output = work / OUTPUT_NAME
        pdf_bytes = output.read_bytes() if output.is_file() else b""
    if not pdf_bytes.startswith(PDF_SIGNATURE):
        raise ConversionError
    return pdf_bytes
