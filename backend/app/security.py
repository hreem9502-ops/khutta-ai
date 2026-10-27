"""Access control for staff-only endpoints."""

from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, Header

from app.config import Settings, get_settings
from app.errors import AdminDisabledError, UnauthorizedError


def require_admin(
    settings: Annotated[Settings, Depends(get_settings)],
    x_admin_token: Annotated[str | None, Header()] = None,
) -> None:
    """Allow the request only if it carries the configured admin token.

    Admin endpoints are disabled entirely while ``ADMIN_TOKEN`` is unset.
    """
    if not settings.admin_token:
        raise AdminDisabledError("Set ADMIN_TOKEN to enable admin endpoints")
    if not x_admin_token or not compare_digest(x_admin_token, settings.admin_token):
        raise UnauthorizedError("Missing or wrong X-Admin-Token header")
