from django.http.response import Http404
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from root.utils.base import fail


def exception_handler(exc: Exception, context: dict):
    """
    Handles exceptions by returning a standardized error response.

    Args:
        exc (Exception): The exception instance to handle.
        context (dict): Additional context about the exception.

    Returns:
        Response: A response object containing the error details and appropriate HTTP status code.
    """
    if isinstance(exc, APIException):
        return Response(fail(exc.detail), status=exc.status_code)
    elif isinstance(exc, Http404):
        return Response(fail(str(exc)), status=404)
    return Response(fail(str(exc)), status=500)
