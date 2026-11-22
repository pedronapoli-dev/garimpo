from typing import Any

from app.schemas import ErrorOut

_ERROR_SCHEMA = {"$ref": "#/components/schemas/ErrorOut"}


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """Documents each error status with ErrorOut, so the generated types know it."""
    return {status_code: {"model": ErrorOut} for status_code in status_codes}


def json_error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """error_responses for a streaming route.

    FastAPI documents extra responses with the route's media type, which for an
    EventSourceResponse is text/event-stream. Errors are raised before the
    stream starts, so they are JSON; say so explicitly.
    """
    return {
        status_code: {"content": {"application/json": {"schema": _ERROR_SCHEMA}}}
        for status_code in status_codes
    }
