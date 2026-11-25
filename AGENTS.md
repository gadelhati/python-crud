# Project Guidelines

## Runtime and dependencies

- Support Python versions `>=3.12,<3.16`; use Python 3.12 locally unless a task requires another supported version.
- Declare production dependencies in `pyproject.toml` with compatible upper bounds.
- Install development tools with `python -m pip install -e ".[dev]"`.
- Store configuration in `app/config.py` using `pydantic-settings`; use the `UVICORN_` environment-variable prefix and do not commit `.env` files.

## Application structure

- Keep application startup and router registration in `app/main.py`.
- Centralize rate limiting configuration (`SlowAPI` `Limiter`) in `app/rate_limit.py` and register its exception handler in `app/main.py`.
- Add HTTP endpoints in `app/routers/`, request and response models in `app/schemas/`, business logic in `app/services/`, and persistence concerns in `app/repositories/`.
- Keep static sub-routes such as `/audit` and `/audit/{id}` declared before dynamic `/{id}` routes in all routers, restricting audit endpoints to `AdminUser`.
- Preserve `/health` as a lightweight liveness endpoint unless a task explicitly requires dependency readiness checks.

## Tests and quality

- Add or update pytest tests in `tests/` for every behavior change, including HTTP status codes, rate limiting (`429`), audit trails, and response payloads for endpoint changes.
- Reset the `SlowAPI` limiter state between tests in `tests/conftest.py` (`limiter.reset()`) to prevent cross-test `429` interference.
- Ruff configuration in `pyproject.toml` is authoritative. Run `python -m ruff check .` and `python -m ruff format --check .`.
- Run `python -m pytest -v` after code changes. The CI workflow runs linting, formatting, and tests for Python 3.12 through 3.15.

## Documentation

- Update `README.md` and `.env.example` when setup, supported Python versions, public endpoints, or configuration behavior changes.
- Follow `CONTRIBUTING.md` for local setup, commit conventions, and pull request expectations.
