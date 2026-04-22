"""
Tests for firebase_fastapi_wrapper.

We use a mock firebase_functions module so tests run without the Firebase SDK
being installed (it won't be available in plain pytest environments).
"""

from __future__ import annotations

import json
import sys
import types
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# Minimal firebase_functions stub
# ---------------------------------------------------------------------------


def _make_firebase_stub() -> None:
    """Inject a minimal ``firebase_functions.https_fn`` stub into sys.modules."""
    if "firebase_functions" in sys.modules:
        return  # already present (real SDK)

    class Response:  # noqa: D101
        def __init__(self, response: Any, status: int = 200, headers: dict | None = None):
            self.response = response
            self.status = status
            self.headers = headers or {}

    class Request:  # noqa: D101
        def __init__(
            self,
            method: str = "GET",
            path: str = "/",
            query_string: bytes = b"",
            headers: dict | None = None,
            data: bytes = b"",
        ):
            self.method = method
            self.path = path
            self.query_string = query_string
            self.headers = headers or {}
            self._data = data

        def get_data(self) -> bytes:
            return self._data

    https_fn_mod = types.SimpleNamespace(Response=Response, Request=Request)
    fb_mod = types.ModuleType("firebase_functions")
    fb_mod.https_fn = https_fn_mod  # type: ignore[attr-defined]
    sys.modules["firebase_functions"] = fb_mod
    sys.modules["firebase_functions.https_fn"] = https_fn_mod  # type: ignore[arg-type]


_make_firebase_stub()

# Import after stub is installed
from firebase_functions import https_fn  # noqa: E402

from firebase_fastapi_wrapper import FastAPIWrapper, __version__  # noqa: E402

# ---------------------------------------------------------------------------
# Shared FastAPI app
# ---------------------------------------------------------------------------


def _build_app() -> FastAPI:
    app = FastAPI()

    @app.get("/hello")
    def hello():
        return {"message": "hello"}

    @app.get("/users/{user_id}")
    def get_user(user_id: str):
        return {"user_id": user_id}

    @app.post("/echo")
    async def echo(body: dict):
        return body

    @app.put("/items/{item_id}")
    async def put_item(item_id: str, body: dict):
        return {"item_id": item_id, **body}

    @app.patch("/items/{item_id}")
    async def patch_item(item_id: str, body: dict):
        return {"item_id": item_id, **body}

    @app.delete("/items/{item_id}")
    async def delete_item(item_id: str):
        return {"deleted": item_id}

    @app.get("/error")
    def raise_error():
        raise ValueError("boom")

    @app.get("/headers-echo")
    async def headers_echo(request: Any = None):
        from fastapi import Request as FastAPIRequest

        async def inner(req: FastAPIRequest):
            return JSONResponse({"x-custom": req.headers.get("x-custom", "")})

        return inner

    @app.get("/query")
    async def query_route(name: str = "", age: int = 0):
        return {"name": name, "age": age}

    return app


@pytest.fixture(scope="module")
def wrapper():
    return FastAPIWrapper(_build_app(), error_include_detail=True)


@pytest.fixture(scope="module")
def raising_wrapper():
    return FastAPIWrapper(_build_app(), raise_on_error=True, error_include_detail=True)


@pytest.fixture(scope="module")
def cors_wrapper():
    return FastAPIWrapper(
        _build_app(),
        cors_origins=["https://example.com"],
        error_include_detail=True,
    )


def _fake_req(
    method: str = "GET",
    path: str = "/",
    query_string: bytes = b"",
    headers: dict | None = None,
    data: bytes = b"",
) -> https_fn.Request:
    return https_fn.Request(
        method=method,
        path=path,
        query_string=query_string,
        headers=headers or {},
        data=data,
    )


# ---------------------------------------------------------------------------
# Tests — basic HTTP verbs
# ---------------------------------------------------------------------------


class TestGetRequests:
    def test_simple_get(self, wrapper):
        req = _fake_req(path="/hello")
        resp = wrapper(req)
        assert resp.status == 200
        assert json.loads(resp.response) == {"message": "hello"}

    def test_path_parameter(self, wrapper):
        req = _fake_req(path="/users/abc123")
        resp = wrapper(req)
        assert resp.status == 200
        assert json.loads(resp.response) == {"user_id": "abc123"}

    def test_not_found(self, wrapper):
        req = _fake_req(path="/does-not-exist")
        resp = wrapper(req)
        assert resp.status == 404

    def test_query_string(self, wrapper):
        req = _fake_req(path="/query", query_string=b"name=Alice&age=30")
        resp = wrapper(req)
        assert resp.status == 200
        assert json.loads(resp.response) == {"name": "Alice", "age": 30}

    def test_query_string_as_str(self, wrapper):
        """query_string can be a plain string too."""
        req = _fake_req(path="/query")
        req.query_string = "name=Bob&age=25"  # type: ignore[assignment]
        resp = wrapper(req)
        assert resp.status == 200
        data = json.loads(resp.response)
        assert data["name"] == "Bob"


class TestPostRequests:
    def test_post_json_body(self, wrapper):
        body = json.dumps({"key": "value"}).encode()
        req = _fake_req(
            method="POST",
            path="/echo",
            headers={"content-type": "application/json"},
            data=body,
        )
        resp = wrapper(req)
        assert resp.status == 200
        assert json.loads(resp.response) == {"key": "value"}


class TestPutAndPatch:
    def test_put_item(self, wrapper):
        body = json.dumps({"name": "widget"}).encode()
        req = _fake_req(
            method="PUT",
            path="/items/42",
            headers={"content-type": "application/json"},
            data=body,
        )
        resp = wrapper(req)
        assert resp.status == 200
        data = json.loads(resp.response)
        assert data["item_id"] == "42"
        assert data["name"] == "widget"

    def test_patch_item(self, wrapper):
        body = json.dumps({"name": "gizmo"}).encode()
        req = _fake_req(
            method="PATCH",
            path="/items/99",
            headers={"content-type": "application/json"},
            data=body,
        )
        resp = wrapper(req)
        assert resp.status == 200
        data = json.loads(resp.response)
        assert data["item_id"] == "99"


class TestDeleteRequests:
    def test_delete_item(self, wrapper):
        req = _fake_req(method="DELETE", path="/items/7")
        resp = wrapper(req)
        assert resp.status == 200
        assert json.loads(resp.response) == {"deleted": "7"}


# ---------------------------------------------------------------------------
# Tests — error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_500_returns_json(self, wrapper):
        req = _fake_req(path="/error")
        resp = wrapper(req)
        # FastAPI itself returns 500; wrapper should not crash
        assert resp.status >= 500

    def test_wrapper_exception_returns_500_json(self, wrapper):
        """Simulate a wrapper-level crash by making a POST whose get_data() raises."""
        bad_req = MagicMock()
        bad_req.method = "POST"  # POST triggers get_data(), causing the crash
        bad_req.path = "/echo"
        bad_req.query_string = None
        bad_req.headers = {"content-type": "application/json"}
        bad_req.get_data.side_effect = RuntimeError("disk read error")

        resp = wrapper(bad_req)
        assert resp.status == 500
        body = json.loads(resp.response)
        assert "error" in body
        assert "request_id" in body
        assert "detail" in body  # error_include_detail=True

    def test_raise_on_error(self, raising_wrapper):
        """raise_on_error=True should let exceptions propagate."""
        bad_req = MagicMock()
        bad_req.method = "POST"  # POST triggers get_data(), causing the crash
        bad_req.path = "/echo"
        bad_req.query_string = None
        bad_req.headers = {"content-type": "application/json"}
        bad_req.get_data.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            raising_wrapper(bad_req)


# ---------------------------------------------------------------------------
# Tests — CORS
# ---------------------------------------------------------------------------


class TestCORS:
    def test_cors_header_injected(self, cors_wrapper):
        req = _fake_req(path="/hello", headers={"Origin": "https://example.com"})
        resp = cors_wrapper(req)
        assert resp.status == 200
        assert resp.headers.get("Access-Control-Allow-Origin") == "https://example.com"

    def test_cors_not_injected_for_unknown_origin(self, cors_wrapper):
        req = _fake_req(path="/hello", headers={"Origin": "https://evil.com"})
        resp = cors_wrapper(req)
        assert "Access-Control-Allow-Origin" not in resp.headers

    def test_cors_not_injected_without_origin(self, cors_wrapper):
        req = _fake_req(path="/hello")
        resp = cors_wrapper(req)
        assert "Access-Control-Allow-Origin" not in resp.headers


# ---------------------------------------------------------------------------
# Tests — metadata
# ---------------------------------------------------------------------------


class TestMetadata:
    def test_version_string(self):
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_repr(self, wrapper):
        r = repr(wrapper)
        assert "FastAPIWrapper" in r
        assert "timeout" in r

    def test_import_from_top_level(self):
        from firebase_fastapi_wrapper import FastAPIWrapper as FW  # noqa: F401

        assert FW is FastAPIWrapper
