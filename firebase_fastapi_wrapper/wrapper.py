"""
firebase_fastapi_wrapper.wrapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Adapts a FastAPI (ASGI) application to run inside a Firebase HTTPS Function.

Typical usage::

    from fastapi import FastAPI
    from firebase_functions import https_fn
    from firebase_fastapi_wrapper import FastAPIWrapper

    app = FastAPI()

    @app.get("/hello")
    def hello():
        return {"message": "Hello from FastAPI!"}

    firebase_handler = FastAPIWrapper(app)

    @https_fn.on_request()
    def handle_request(req: https_fn.Request) -> https_fn.Response:
        return firebase_handler(req)
"""

from __future__ import annotations

import json
import logging
import traceback
import uuid
from collections.abc import Sequence
from typing import Any

from starlette.testclient import TestClient

logger = logging.getLogger("firebase_fastapi_wrapper")

# HTTP methods that can carry a request body
_BODY_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class FastAPIWrapper:
    """Wraps a FastAPI/ASGI app to serve Firebase HTTPS function requests.

    Args:
        app: The FastAPI (or any ASGI-compatible) application instance.
        raise_on_error: When ``True`` exceptions bubble up instead of being
            converted to a 500 JSON response.  Useful in tests.
        timeout: Request timeout in seconds forwarded to the underlying
            :class:`~starlette.testclient.TestClient`.  Defaults to 30 s.
        cors_origins: Optional list of allowed CORS origins.  When provided,
            the wrapper injects ``Access-Control-Allow-Origin`` / method /
            headers response headers automatically.
        error_include_detail: When ``True`` (default in development, set
            ``False`` in production) the 500 error body includes the
            exception message.

    Example::

        wrapper = FastAPIWrapper(
            app,
            timeout=60,
            cors_origins=["https://example.com"],
            error_include_detail=False,  # hide internals in production
        )
    """

    def __init__(
        self,
        app: Any,
        *,
        raise_on_error: bool = False,
        timeout: float = 30.0,
        cors_origins: Sequence[str] | None = None,
        error_include_detail: bool = True,
    ) -> None:
        self.app = app
        self.raise_on_error = raise_on_error
        self.timeout = timeout
        self.cors_origins: list[str] = list(cors_origins) if cors_origins else []
        self.error_include_detail = error_include_detail
        self._client = TestClient(app, raise_server_exceptions=raise_on_error)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def __call__(self, req: Any) -> Any:  # returns firebase_functions.https_fn.Response
        """Forward a Firebase ``https_fn.Request`` to the wrapped FastAPI app.

        Args:
            req: A ``firebase_functions.https_fn.Request`` object.

        Returns:
            A ``firebase_functions.https_fn.Response`` object.
        """
        from firebase_functions import https_fn  # local import keeps tests independent

        request_id = str(uuid.uuid4())
        logger.info(
            "request_id=%s method=%s path=%s",
            request_id,
            req.method,
            req.path,
        )

        try:
            return self._forward(req, request_id, https_fn)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "request_id=%s Unhandled error: %s\n%s",
                request_id,
                exc,
                traceback.format_exc(),
            )
            if self.raise_on_error:
                raise
            return self._error_response(https_fn, request_id, exc)

    def __repr__(self) -> str:
        return (
            f"FastAPIWrapper(app={self.app!r}, "
            f"timeout={self.timeout}, "
            f"cors_origins={self.cors_origins!r})"
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _forward(self, req: Any, request_id: str, https_fn: Any) -> Any:
        """Build and dispatch the request to the TestClient."""
        path: str = req.path or "/"
        query: str = ""
        if hasattr(req, "query_string") and req.query_string:
            raw_qs = req.query_string
            query = raw_qs.decode("utf-8") if isinstance(raw_qs, bytes) else str(raw_qs)
        full_url = f"{path}?{query}" if query else path

        headers = dict(req.headers)
        # Remove hop-by-hop headers that must not be forwarded
        for hop in ("host", "transfer-encoding", "connection"):
            headers.pop(hop, None)

        body: bytes | None = None
        if req.method.upper() in _BODY_METHODS:
            body = req.get_data()

        logger.debug("request_id=%s → %s %s", request_id, req.method, full_url)

        response = self._client.request(
            method=req.method,
            url=full_url,
            headers=headers,
            content=body,
        )

        resp_headers = dict(response.headers)
        self._inject_cors(req, resp_headers)

        logger.info(
            "request_id=%s ← status=%s",
            request_id,
            response.status_code,
        )
        return https_fn.Response(
            response=response.content,
            status=response.status_code,
            headers=resp_headers,
        )

    def _inject_cors(self, req: Any, headers: dict[str, str]) -> None:
        """Add CORS headers when ``cors_origins`` is configured."""
        if not self.cors_origins:
            return
        origin = req.headers.get("Origin", "")
        if origin in self.cors_origins or "*" in self.cors_origins:
            headers["Access-Control-Allow-Origin"] = origin or "*"
            headers.setdefault(
                "Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            )
            headers.setdefault(
                "Access-Control-Allow-Headers",
                "Authorization, Content-Type, X-Requested-With",
            )

    def _error_response(self, https_fn: Any, request_id: str, exc: Exception) -> Any:
        """Build a structured JSON 500 error response."""
        body: dict[str, Any] = {
            "error": "Internal Server Error",
            "request_id": request_id,
        }
        if self.error_include_detail:
            body["detail"] = str(exc)
        return https_fn.Response(
            response=json.dumps(body),
            status=500,
            headers={"Content-Type": "application/json"},
        )
