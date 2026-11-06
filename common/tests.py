from django.conf import settings
from django.test import SimpleTestCase, override_settings

HEALTH_URL = "/api/v1/health/"
UI_ORIGIN = "http://localhost:5173"
OTHER_ORIGIN = "http://evil.example"


@override_settings(CORS_ALLOWED_ORIGINS=[UI_ORIGIN])
class CorsTests(SimpleTestCase):
    def test_listed_origin_is_allowed(self):
        response = self.client.get(HEALTH_URL, HTTP_ORIGIN=UI_ORIGIN)
        self.assertEqual(response["Access-Control-Allow-Origin"], UI_ORIGIN)

    def test_unlisted_origin_gets_no_cors_headers(self):
        response = self.client.get(HEALTH_URL, HTTP_ORIGIN=OTHER_ORIGIN)
        self.assertNotIn("Access-Control-Allow-Origin", response)

    def test_preflight_for_authorization_header_is_answered(self):
        response = self.client.options(
            HEALTH_URL,
            HTTP_ORIGIN=UI_ORIGIN,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], UI_ORIGIN)
        self.assertIn("authorization", response["Access-Control-Allow-Headers"])

    def test_non_api_paths_get_no_cors_headers(self):
        response = self.client.get("/admin/login/", HTTP_ORIGIN=UI_ORIGIN)
        self.assertNotIn("Access-Control-Allow-Origin", response)

    @override_settings(CORS_ALLOWED_ORIGINS=[])
    def test_no_origins_allowed_by_default(self):
        response = self.client.get(HEALTH_URL, HTTP_ORIGIN=UI_ORIGIN)
        self.assertNotIn("Access-Control-Allow-Origin", response)

    def test_never_a_wildcard(self):
        self.assertFalse(getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False))
        self.assertNotIn("*", settings.CORS_ALLOWED_ORIGINS)
