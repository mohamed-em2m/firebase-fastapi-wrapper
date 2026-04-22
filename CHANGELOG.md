# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] — 2026-04-22

### Added
- `cors_origins` parameter — built-in CORS header injection per allow-list.
- `timeout` parameter — configurable per-request timeout (default 30 s).
- `error_include_detail` parameter — control whether exception messages appear in 500 responses.
- `raise_on_error` parameter — raise exceptions instead of catching them (useful in tests).
- `firebase_fastapi_wrapper/__init__.py` — top-level imports (`FastAPIWrapper`, `__version__`).
- `firebase_fastapi_wrapper/py.typed` — PEP 561 typed-package marker.
- `tests/test_wrapper.py` — full pytest test suite with self-contained Firebase stub.
- New `[project.optional-dependencies] dev` group in `pyproject.toml`.
- CI matrix across Python 3.10, 3.11, 3.12.
- Dedicated `pre-commit.yml` CI workflow.
- `CONTRIBUTING.md` contributor guide.

### Changed
- Renamed `" wrapper.py"` → `wrapper.py` (removed accidental leading space).
- Error responses are now structured JSON with a `request_id` field (was plain text).
- `DELETE` and `HEAD` requests now correctly forward their body.
- `publish.yml` now triggers on GitHub Release (not every push to `main`).
- `python-app.yml` uses `ruff` + `uv` (replaced `flake8` + `pip`).
- SLSA workflow builds real wheel/sdist artifacts (replaced placeholder files).
- Widened `requires-python` from `>=3.12` to `>=3.10`.
- Bumped version `0.1.2 → 0.2.0`.

### Fixed
- Hop-by-hop headers (`host`, `connection`, `transfer-encoding`) are no longer forwarded.
- `query_string` is handled correctly whether bytes or str.

---

## [0.1.2] — Initial release

- Basic `FastAPIWrapper` wrapping a FastAPI app with a `starlette.testclient.TestClient`.
- Forwarding of `GET`, `POST`, `PUT`, `PATCH` requests.
- Simple logging and plain-text 500 error fallback.
