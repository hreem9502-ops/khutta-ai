"""Domain errors and their HTTP mapping.

Every error carries a stable machine-readable ``code``; the frontend translates it into
a localised message, so ``detail`` is only a developer-facing hint.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    """Base class for errors that map to a client-visible HTTP response."""

    status_code = 400
    code = "bad_request"

    def __init__(self, detail: str = "") -> None:
        super().__init__(detail or self.code)
        self.detail = detail or self.code


class DepartmentNotFoundError(DomainError):
    status_code = 404
    code = "department_not_found"


class UnknownCourseError(DomainError):
    status_code = 422
    code = "unknown_course"


class InvalidTranscriptError(DomainError):
    status_code = 400
    code = "invalid_pdf"


class UnreadableTranscriptError(DomainError):
    status_code = 422
    code = "no_text_in_pdf"


class FileTooLargeError(DomainError):
    status_code = 413
    code = "file_too_large"


class PlanStorageUnavailableError(DomainError):
    """The plan store cannot be written, e.g. a read-only serverless disk without Redis."""

    status_code = 503
    code = "plan_storage_unavailable"


class AdminDisabledError(DomainError):
    status_code = 403
    code = "admin_disabled"


class UnauthorizedError(DomainError):
    status_code = 401
    code = "unauthorized"


class AIServiceError(Exception):
    """An AI call failed or returned an unusable answer. Callers fall back to rules; never reaches the client."""


def register_error_handlers(app: FastAPI) -> None:
    """Attach the :class:`DomainError` handler to ``app``."""

    @app.exception_handler(DomainError)
    async def _handle_domain_error(_: Request, error: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"error": {"code": error.code, "detail": error.detail}},
        )
