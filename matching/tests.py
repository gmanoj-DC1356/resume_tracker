import io

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from resumes.models import Resume
from resumes.signals import RECRUITER_GROUP

from .models import CandidateProfile

CANDIDATES_URL = "/api/v1/matching/candidates/"
DENIED = (401, 403)


def make_resume(name, filename="cv.pdf", status=Resume.Status.READY) -> Resume:
    return Resume.objects.create(
        candidate_name=name,
        original_filename=filename,
        file_type=Resume.FileType.PDF,
        status=status,
        size_bytes=1,
        original_file=f"resumes/test/{filename}",
    )


def make_profile(resume: Resume, role="Data Engineer", years=5) -> CandidateProfile:
    return CandidateProfile.objects.create(
        resume=resume, role_title=role, years_experience=years, skills=["Python", "SQL"], summary="Synthetic."
    )


class CandidateListTests(TestCase):
    def setUp(self):
        self.recruiter = get_user_model().objects.create_user("recruiter")
        self.recruiter.groups.add(Group.objects.get(name=RECRUITER_GROUP))
        self.outsider = get_user_model().objects.create_user("outsider")
        self.client = APIClient()

    def test_requires_login_and_recruiter_permission(self):
        self.assertIn(self.client.get(CANDIDATES_URL).status_code, DENIED)
        self.client.force_authenticate(self.outsider)
        self.assertEqual(self.client.get(CANDIDATES_URL).status_code, 403)

    def test_lists_candidate_cards(self):
        resume = make_resume("Candidate T")
        make_profile(resume, role="Data Engineer", years=8)
        self.client.force_authenticate(self.recruiter)
        response = self.client.get(CANDIDATES_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        card = response.json()["results"][0]
        self.assertEqual(card["resume_id"], str(resume.id))
        self.assertEqual(card["name"], "Candidate T")
        self.assertEqual(card["role_title"], "Data Engineer")
        self.assertEqual(card["years_experience"], 8)
        self.assertEqual(card["skills"], ["Python", "SQL"])
        self.assertNotIn("original_file", card)  # no storage paths

    def test_resumes_that_cannot_be_opened_are_not_listed(self):
        make_profile(make_resume("Broken", status=Resume.Status.FAILED))
        make_resume("No profile yet")
        self.client.force_authenticate(self.recruiter)
        self.assertEqual(self.client.get(CANDIDATES_URL).data["count"], 0)


class LoadSampleCandidatesTests(TestCase):
    def run_command(self):
        call_command("load_sample_candidates", stdout=io.StringIO())

    @override_settings(DEBUG=True)
    def test_creates_profiles_once_for_sample_resumes(self):
        make_resume("Candidate A", filename="candidate_a.pdf")
        make_resume("Candidate Other", filename="not_a_sample.pdf")
        self.run_command()
        self.run_command()  # safe to repeat
        self.assertEqual(CandidateProfile.objects.count(), 1)
        self.assertEqual(CandidateProfile.objects.get().role_title, "Data Engineer")

    @override_settings(DEBUG=True)
    def test_explains_when_resumes_are_missing(self):
        with self.assertRaises(CommandError):
            self.run_command()

    @override_settings(DEBUG=False)
    def test_refuses_outside_debug(self):
        make_resume("Candidate A", filename="candidate_a.pdf")
        with self.assertRaises(CommandError):
            self.run_command()
        self.assertEqual(CandidateProfile.objects.count(), 0)
