import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return response

    view = context.get("view")
    view_name = view.__class__.__name__ if view is not None else "unknown"
    method = getattr(context.get("request"), "method", "unknown")
    logger.exception("Unhandled server error in view=%s method=%s", view_name, method)
    return Response({"error": "Server xatosi yuz berdi"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
