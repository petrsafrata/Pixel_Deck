from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException, Request, status


def require_api_token(
    request: Request,
    x_api_token: Optional[str] = Header(default=None, alias="X-API-Token"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> None:
    """
    Validate the API token for a protected endpoint.

    The token is compared against the value currently loaded in the
    application's runtime configuration. Clients may authenticate using
    either the `X-API-Token` header or a standard Bearer token.

    Args:
        request: Current FastAPI request.
        x_api_token: Token supplied using the custom `X-API-Token` header.
        authorization: Standard HTTP Authorization header.

    Raises:
        HTTPException(503):
            No API token is configured in the application.

        HTTPException(401):
            The supplied token is missing or invalid.
    """

    runtime = getattr(request.app.state, "runtime", None)
    token = ""
    if runtime is not None:
        token = getattr(runtime.web, "api_token", "")

    if not token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="API token not configured")

    if x_api_token and x_api_token == token:
        return

    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization.split(" ", 1)[1].strip()
        if bearer == token:
            return

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token")
