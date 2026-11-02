"""Shared API error handling. Returns one consistent error shape and never leaks internals."""
import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        # Unhandled error: log server-side, return a generic message (fail closed).
        logger.exception("Unhandled API error", exc_info=exc)
        return Response({"error": {"code": "server_error", "detail": "Internal server error."}}, status=500)
    response.data = {"error": {"code": getattr(exc, "default_code", "error"), "detail": response.data}}
    return response
