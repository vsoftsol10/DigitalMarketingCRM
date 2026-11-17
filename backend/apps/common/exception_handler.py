import logging

from rest_framework.views import exception_handler

from .responses import error_response


logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(
        exc,
        context,
    )

    if response is None:
        logger.exception(
            "Unhandled API exception",
            exc_info=exc,
        )

        return error_response(
            message="Internal Server Error",
            status_code=500,
        )

    message = response.data.get(
        "detail",
        "Validation Error",
    )

    wrapped_response = error_response(
        message=str(message),
        errors=response.data,
        status_code=response.status_code,
    )

    # Preserve headers that carry API behavior while retaining the project
    # envelope. Avoid copying representation headers such as Content-Length,
    # which may no longer describe the wrapped response body.
    for header in (
        "Retry-After",
        "WWW-Authenticate",
        "Proxy-Authenticate",
        "Allow",
        "Vary",
    ):
        if header in response:
            wrapped_response[header] = response[header]

    return wrapped_response
