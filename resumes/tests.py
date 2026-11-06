import io
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path
from unittest import skipUnless

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import Resume
from .signals import RECRUITER_GROUP

PDF_BYTES = b"%PDF-1.4\n% synthetic test file\n"
COLLECTION_URL = "/api/v1/resumes/"
LIBREOFFICE_AVAILABLE = shutil.which(settings.LIBREOFFICE_BIN) is not None
DENIED = (401, 403)


def make_docx(extra_parts=None, include_document=True) -> bytes:
    """Build a tiny valid Word file from synthetic text."""
    namespace = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    parts = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>"
        ),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>"
        ),
    }
    if include_document:
        parts["word/document.xml"] = (
            f'<?xml version="1.0" encoding="UTF-8"?><w:document {namespace}><w:body>'
            "<w:p><w:r><w:t>Synthetic resume for tests</w:t></w:r></w:p></w:body></w:document>"
        )
    parts.update(extra_parts or {})
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            archive.writestr(name, content)
    return buffer.getvalue()


class ResumeApiTestCase(TestCase):
    def setUp(self):
        media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        override = override_settings(MEDIA_ROOT=media_root)
        override.enable()
        self.addCleanup(override.disable)

        user_model = get_user_model()
        self.recruiter = user_model.objects.create_user("recruiter")
        self.recruiter.groups.add(Group.objects.get(name=RECRUITER_GROUP))
        self.other_recruiter = user_model.objects.create_user("other_recruiter")
        self.other_recruiter.groups.add(Group.objects.get(name=RECRUITER_GROUP))
        self.outsider = user_model.objects.create_user("outsider")  # logged in, not a recruiter
        self.client = APIClient()

    def login(self, user):
        self.client.force_authenticate(user)

    def upload(self, filename="cv.pdf", content=PDF_BYTES, name="Candidate T"):
        data = {"candidate_name": name, "file": SimpleUploadedFile(filename, content)}
        return self.client.post(COLLECTION_URL, data, format="multipart")

    def create_resume(self, user=None, filename="cv.pdf", content=PDF_BYTES) -> Resume:
        self.login(user or self.recruiter)
        response = self.upload(filename=filename, content=content)
        self.assertEqual(response.status_code, 201, response.content)
        self.client.force_authenticate(None)
        return Resume.objects.get(pk=response.data["id"])


class RecruiterGroupTests(ResumeApiTestCase):
    def test_group_has_view_and_add_permissions(self):
        codenames = set(Group.objects.get(name=RECRUITER_GROUP).permissions.values_list("codename", flat=True))
        self.assertLessEqual({"view_resume", "add_resume"}, codenames)


class UploadTests(ResumeApiTestCase):
    def test_anonymous_cannot_upload(self):
        self.assertIn(self.upload().status_code, DENIED)

    def test_user_without_recruiter_permission_gets_403(self):
        self.login(self.outsider)
        self.assertEqual(self.upload().status_code, 403)
        self.assertEqual(Resume.objects.count(), 0)

    def test_recruiter_uploads_pdf(self):
        self.login(self.recruiter)
        response = self.upload()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "ready")
        self.assertEqual(response.data["file_type"], "pdf")
        self.assertNotIn("original_file", response.data)  # no storage paths in responses
        resume = Resume.objects.get(pk=response.data["id"])
        self.assertEqual(resume.uploaded_by, self.recruiter)
        self.assertEqual(resume.original_file.name, f"resumes/{resume.id}/original.pdf")
        self.assertTrue(default_storage.exists(resume.original_file.name))

    def test_stored_name_never_comes_from_the_uploaded_name(self):
        self.login(self.recruiter)
        response = self.upload(filename="../../evil.pdf")
        self.assertEqual(response.status_code, 201)
        resume = Resume.objects.get(pk=response.data["id"])
        self.assertEqual(resume.original_file.name, f"resumes/{resume.id}/original.pdf")
        self.assertNotIn("..", resume.original_filename)

    def test_rejects_wrong_extension(self):
        self.login(self.recruiter)
        self.assertEqual(self.upload(filename="cv.exe").status_code, 415)

    def test_rejects_fake_pdf(self):
        self.login(self.recruiter)
        self.assertEqual(self.upload(content=b"not really a pdf").status_code, 415)

    def test_rejects_fake_docx(self):
        self.login(self.recruiter)
        self.assertEqual(self.upload(filename="cv.docx", content=b"not a zip").status_code, 415)

    def test_rejects_zip_that_is_not_word(self):
        self.login(self.recruiter)
        content = make_docx(include_document=False)
        self.assertEqual(self.upload(filename="cv.docx", content=content).status_code, 415)

    @override_settings(RESUME_MAX_UNCOMPRESSED_BYTES=100)
    def test_rejects_docx_that_expands_too_much(self):
        self.login(self.recruiter)
        content = make_docx(extra_parts={"word/big.xml": "0" * 5000})
        self.assertEqual(self.upload(filename="cv.docx", content=content).status_code, 415)

    @override_settings(RESUME_MAX_UPLOAD_BYTES=100)
    def test_rejects_file_over_size_limit(self):
        self.login(self.recruiter)
        self.assertEqual(self.upload(content=PDF_BYTES + b"x" * 200).status_code, 413)

    @override_settings(RESUME_MAX_UPLOAD_BYTES=100)
    def test_rejects_huge_request_before_parsing(self):
        self.login(self.recruiter)
        response = self.upload(content=PDF_BYTES + b"x" * 100_000)
        self.assertEqual(response.status_code, 413)
        self.assertEqual(Resume.objects.count(), 0)

    def test_requires_candidate_name_and_file(self):
        self.login(self.recruiter)
        no_name = self.client.post(COLLECTION_URL, {"file": SimpleUploadedFile("cv.pdf", PDF_BYTES)}, format="multipart")
        no_file = self.client.post(COLLECTION_URL, {"candidate_name": "Candidate T"}, format="multipart")
        bad_name = self.upload(name="Bad\x07Name")
        for response in (no_name, no_file, bad_name):
            self.assertEqual(response.status_code, 400)
            self.assertIn("error", response.json())

    def test_json_body_is_not_accepted(self):
        self.login(self.recruiter)
        response = self.client.post(COLLECTION_URL, {"candidate_name": "x"}, format="json")
        self.assertEqual(response.status_code, 415)

    @skipUnless(LIBREOFFICE_AVAILABLE, "LibreOffice is not installed")
    def test_word_file_is_converted_to_a_viewable_pdf(self):
        resume = self.create_resume(filename="cv.docx", content=make_docx())
        self.assertEqual(resume.status, Resume.Status.READY)
        self.assertEqual(resume.pdf_file.name, f"resumes/{resume.id}/viewable.pdf")
        self.login(self.recruiter)
        response = self.client.get(f"{COLLECTION_URL}{resume.id}/file/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"".join(response.streaming_content).startswith(b"%PDF-"))

    @override_settings(LIBREOFFICE_BIN="definitely-not-installed-converter")
    def test_failed_conversion_is_recorded_and_file_is_unreadable(self):
        resume = self.create_resume(filename="cv.docx", content=make_docx())
        self.assertEqual(resume.status, Resume.Status.FAILED)
        self.login(self.recruiter)
        self.assertEqual(self.client.get(f"{COLLECTION_URL}{resume.id}/file/").status_code, 422)


class ReadTests(ResumeApiTestCase):
    def test_list_requires_login_and_recruiter_permission(self):
        self.assertIn(self.client.get(COLLECTION_URL).status_code, DENIED)
        self.login(self.outsider)
        self.assertEqual(self.client.get(COLLECTION_URL).status_code, 403)

    def test_every_recruiter_sees_every_resume(self):
        mine = self.create_resume(user=self.recruiter)
        theirs = self.create_resume(user=self.other_recruiter)
        self.login(self.recruiter)
        response = self.client.get(COLLECTION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual({row["id"] for row in response.data["results"]}, {str(mine.id), str(theirs.id)})

    def test_detail_access_rules(self):
        resume = self.create_resume()
        url = f"{COLLECTION_URL}{resume.id}/"
        self.assertIn(self.client.get(url).status_code, DENIED)
        self.login(self.other_recruiter)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.login(self.outsider)
        self.assertEqual(self.client.get(url).status_code, 404)  # same as "does not exist"
        self.login(self.recruiter)
        self.assertEqual(self.client.get(f"{COLLECTION_URL}{uuid.uuid4()}/").status_code, 404)
        self.assertEqual(self.client.get(f"{COLLECTION_URL}12345/").status_code, 404)


class FileEndpointTests(ResumeApiTestCase):
    def setUp(self):
        super().setUp()
        self.resume = self.create_resume(filename="Jane Private CV.pdf")
        self.url = f"{COLLECTION_URL}{self.resume.id}/file/"

    def test_recruiter_gets_the_pdf_with_safe_headers(self):
        self.login(self.recruiter)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(b"".join(response.streaming_content), PDF_BYTES)
        self.assertTrue(response["Content-Disposition"].startswith("inline"))
        self.assertNotIn("Jane", response["Content-Disposition"])  # uploaded name is not echoed
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn("private", response["Cache-Control"])

    def test_accept_header_does_not_cause_406(self):
        self.login(self.recruiter)
        self.assertEqual(self.client.get(self.url, HTTP_ACCEPT="application/pdf").status_code, 200)

    def test_anonymous_and_non_recruiters_cannot_read(self):
        self.assertIn(self.client.get(self.url).status_code, DENIED)
        self.login(self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_missing_stored_file_returns_422(self):
        default_storage.delete(self.resume.pdf_file.name)
        self.login(self.recruiter)
        self.assertEqual(self.client.get(self.url).status_code, 422)

    def test_deleting_a_resume_deletes_its_files(self):
        name = self.resume.original_file.name
        self.assertTrue(default_storage.exists(name))
        self.resume.delete()
        self.assertFalse(default_storage.exists(name))


class LoadSampleResumesCommandTests(ResumeApiTestCase):
    def run_command(self, directory):
        call_command(
            "load_sample_resumes", "--username", "recruiter", "--directory", str(directory),
            stdout=io.StringIO(), stderr=io.StringIO(),
        )

    def sample_dir(self) -> Path:
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        (directory / "candidate_z.pdf").write_bytes(PDF_BYTES)
        return directory

    @override_settings(DEBUG=True)
    def test_loads_samples_once(self):
        directory = self.sample_dir()
        self.run_command(directory)
        self.run_command(directory)  # second run skips what is already loaded
        self.assertEqual(Resume.objects.filter(candidate_name="Candidate Z").count(), 1)

    @override_settings(DEBUG=False)
    def test_refuses_outside_debug(self):
        with self.assertRaises(CommandError):
            self.run_command(self.sample_dir())
        self.assertEqual(Resume.objects.count(), 0)
