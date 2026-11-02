"""Interview question generation, chatbot & feedback.

Owner: TBD (Phase 2)
Pattern to follow: serializer -> view -> permission check -> url -> test.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def ping(request):
    # IsAuthenticated is the project default. Add object-level checks for real endpoints.
    return Response({"app": "interview", "status": "ok"})
