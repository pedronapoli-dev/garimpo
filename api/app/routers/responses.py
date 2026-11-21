from typing import Any

from app.schemas import ErrorOut


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """Documents each error status with ErrorOut, so the generated types know it."""
    return {status_code: {"model": ErrorOut} for status_code in status_codes}
