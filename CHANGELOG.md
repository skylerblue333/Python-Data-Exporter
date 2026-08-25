# Changelog

## 0.1.0 - 2026-08-24

- Preserve and harden the existing SQLite data-export concept instead of the unrelated placeholder service.
- Add read-only SQLite mode, query-only enforcement, single-statement SELECT/WITH validation, parameter support, and result bounds.
- Add atomic JSON/CSV output and explicit overwrite controls.
- Remove unused FastAPI/uvicorn runtime dependencies and the fake processing API.
- Add deterministic library/CLI tests, Ruff, pytest, pip-audit, CLI smoke testing, Docker build, and non-root verification.
- Document engineering-beta scope and data-authorization boundaries.
