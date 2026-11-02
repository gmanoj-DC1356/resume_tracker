from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])  # explicit opt-out: liveness probe for devops, exposes no data
def health(request):
    return Response({"status": "ok"})
