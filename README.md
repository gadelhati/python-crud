<div align="center">

# _Python CRUD_

[![GitHub stars](https://img.shields.io/github/stars/forgepack/python-crud?style=social)](https://github.com/forgepack/python-crud)
[![GitHub forks](https://img.shields.io/github/forks/forgepack/python-crud?style=social)](https://github.com/forgepack/python-crud/fork)
[![GitHub watchers](https://img.shields.io/github/watchers/forgepack/python-crud?style=social)](https://github.com/forgepack/python-crud)

[![CI](https://github.com/forgepack/python-crud/actions/workflows/ci.yml/badge.svg)](https://github.com/forgepack/python-crud/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/forgepack/python-crud/blob/main/LICENSE.md)

</div>

Production-ready FastAPI core boilerplate featuring **JWT Authentication**, **Refresh Token Rotation & Blacklist**, **Granular RBAC (Roles & Permissions)**, **Brute-Force Lockout**, **Distributed Rate Limiting**, **Audit Trails**, **Soft Delete**, and **Optimistic Concurrency Control**.

Designed as a foundational platform to plug in modular Python services and microservices under a unified authentication and authorization layer.

## Project Structure

```text
python-crud/
├── alembic/                  # Database migrations
├── app/
│   ├── enums/                # Permission and domain enums
│   ├── models/               # SQLAlchemy ORM models
│   ├── repositories/         # Data access layer with soft-delete support
│   ├── routers/              # FastAPI route handlers (admin, auth, base, user, role, permission)
│   ├── schemas/              # Pydantic request/response and audit schemas
│   ├── services/             # Business logic, password hashing, JWT, and audit services
│   ├── config.py             # Pydantic Settings configuration (UVICORN_ prefix)
│   ├── database.py           # Engine and SessionLocal setup
│   ├── dependencies.py       # Auth, RBAC, and DB session dependencies
│   ├── main.py               # FastAPI app initialization, lifespan, and exception handlers
│   └── rate_limit.py         # SlowAPI Limiter instance
├── tests/                    # Pytest test suite
├── .env.example              # Environment variable template
├── AGENTS.md                 # AI and contributor coding guidelines
├── CONTRIBUTING.md           # Contribution workflow and standards
└── pyproject.toml            # Dependencies and Ruff configuration
```

## Tech Stack

![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-3.54.1-blue?logo=sqlite&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17.5-blue?logo=postgresql)

---

## Key Features

- **Authentication & Token Security:**
  - PBKDF2-HMAC-SHA256 password hashing with random salts.
  - Access and refresh JWT tokens with `jti` tracking, database-backed token blacklisting, automatic token rotation on refresh, and immediate rejection of deactivated accounts.
  - Account lockout after consecutive failed login attempts (`423 Locked`), with administrative unlock support.
- **Rate Limiting (`SlowAPI`):**
  - Centralized limiter configuration in `app/rate_limit.py` supporting in-memory (`memory://`) or Redis (`redis://`) backends.
  - Configurable rate limits on critical endpoints (`POST /login`, `POST /login/refresh`, and `POST /admin/init/create-first-user`) returning `429 Too Many Requests`.
- **RBAC & Unified Audit Trails:**
  - Granular permission synchronization (`EnumPermissionAction`) across users, roles, and permissions.
  - Standardized audit endpoints (`GET /user/audit`, `GET /user/audit/{id}`, `GET /role/audit`, `GET /role/audit/{id}`, `GET /permission/audit`, `GET /permission/audit/{id}`) restricted to administrators (`AdminUser`), exposing `created_by`, `updated_by`, `deleted_by`, `deleted_at`, and `version_id` (including soft-deleted records).
- **Data Layer & Concurrency:**
  - Generic repository and service patterns (`ServiceBase` with `get_audit` and `list_audit`) built on SQLAlchemy 2.0.
  - Alembic database migrations supporting SQLite and PostgreSQL.
  - Soft delete, restore, hard delete, and optimistic locking (`version_id`).

## Endpoints

### Public & Bootstrap
- `GET /` — Root welcome response
- `GET /health` — Lightweight liveness check
- `POST /admin/init/create-first-user` — Bootstrap initial administrator account (rate-limited)

### Authentication
- `POST /login` — Authenticate and issue access + refresh tokens (rate-limited)
- `POST /login/refresh` — Rotate refresh token and issue new token pair (rate-limited)
- `POST /login/logout` — Revoke refresh token in blacklist

### Users, Roles & Permissions
- `GET /user`, `POST /user`, `GET /user/{user_id}`, `PUT /user/{user_id}`, `DELETE /user/{user_id}`, `PATCH /user/{user_id}/restore`, `DELETE /user/{user_id}/hard`, `POST /user/{user_id}/unlock`
- `GET /role`, `POST /role`, `GET /role/{role_id}`, `PUT /role/{role_id}`, `DELETE /role/{role_id}`, `PATCH /role/{role_id}/restore`, `DELETE /role/{role_id}/hard`
- `GET /permission`, `POST /permission`, `GET /permission/{permission_id}`, `PUT /permission/{permission_id}`, `DELETE /permission/{permission_id}`, `PATCH /permission/{permission_id}/restore`, `DELETE /permission/{permission_id}/hard`

### Audit Endpoints (`AdminUser` only)
- `GET /user/audit` and `GET /user/audit/{user_id}`
- `GET /role/audit` and `GET /role/audit/{role_id}`
- `GET /permission/audit` and `GET /permission/audit/{permission_id}`

## Configuration

Copy `.env.example` to `.env` and configure the environment variables:

### _Windows PowerShell_
```powershell
Copy-Item .env.example .env
```

### _Linux / macOS_
```bash
cp .env.example .env
```

| Variable | Default | Description |
| :--- | :--- | :--- |
| `UVICORN_HOST` | `127.0.0.1` | Server bind host |
| `UVICORN_PORT` | `9000` | Server bind port |
| `UVICORN_ROOT_PATH` | `""` | ASGI root path |
| `UVICORN_RELOAD` | `false` | Enable auto-reload in development |
| `UVICORN_JWT_SECRET_KEY` | *(required)* | Secret key for signing access tokens (min 32 chars) |
| `UVICORN_JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime in minutes |
| `UVICORN_JWT_REFRESH_SECRET_KEY` | `None` | Optional separate secret key for refresh tokens |
| `UVICORN_JWT_REFRESH_TOKEN_EXPIRE_MINUTES` | `10080` | Refresh token lifetime in minutes (7 days) |
| `UVICORN_DATABASE_URL` | *(required)* | SQLAlchemy database connection URL |
| `UVICORN_RATE_LIMIT_STORAGE_URI` | `memory://` | SlowAPI storage backend (`memory://` or `redis://...`) |
| `UVICORN_RATE_LIMIT_LOGIN` | `10/minute` | Rate limit for `POST /login` |
| `UVICORN_RATE_LIMIT_REFRESH` | `10/minute` | Rate limit for `POST /login/refresh` |
| `UVICORN_RATE_LIMIT_BOOTSTRAP` | `3/minute` | Rate limit for `POST /admin/init/create-first-user` |

## Local Setup & Running

This project requires **Python 3.13** (`>=3.13,<3.16`).

```bash
# create virtual environment
# Windows PowerShell
py -3.13 -m venv .venv
# Linux / macOS
python3.13 -m venv .venv

# activate virtual environment (*)
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

# update pip and install dependencies
python -m pip install --upgrade pip

# install dependencies
python -m pip install -e ".[dev]"

# apply the migration to the database
alembic upgrade head

# build wheel artifact
python -m build

# inspect the contents of the wheel
python -m zipfile -l dist/python_crud-1.0.0-py3-none-any.whl

# run application (*)
python -m app.main
```

Interactive API documentation is available at `http://127.0.0.1:9001/docs`.

## Code Quality (Ruff)

```bash
# automatically formats the code to follow the standard
python -m ruff format .

# auto-fix lint issues
python -m ruff check --fix .

# verify formatting and linting (CI checks)
python -m ruff format --check .

# identifies linting issues and potential code errors
python -m ruff check .
```

## Running Tests

```bash
# run tests with verbose output
python -m pytest -v

# run tests with terminal coverage report
python -m pytest --cov=app --cov-report=term-missing

# generate HTML coverage report in /htmlcov/index.html
python -m pytest --cov=app --cov-report=html
```

## Migration creation commands
```bash
# create alembic config
alembic init alembic

# delete file and directory if they exist
Remove-Item -Force -ErrorAction SilentlyContinue db.sqlite3, alembic\versions\*.py

# generates the initial migration file by comparing the models with the database
alembic revision --autogenerate -m "initial schema"

# apply the migration to the database
alembic upgrade head

# generate a new migration after model changes
alembic revision --autogenerate -m "describe change"
```

## DEVELOPERS

### Contributors
> _[Gadelha TI](https://github.com/gadelhati)_ - *Research Software Engineer · Software Architect · Lead Developer*

## LICENSE

This project is licensed under the __MIT License__ — see the [LICENSE.md](LICENSE.md) file for details.

<div align="center">

__⭐ Did you like the project? Leave a star! ⭐__

[![GitHub stars](https://img.shields.io/github/stars/forgepack/python-crud?style=social)](https://github.com/forgepack/python-crud)
[![GitHub forks](https://img.shields.io/github/forks/forgepack/python-crud?style=social)](https://github.com/forgepack/python-crud/fork)
[![GitHub watchers](https://img.shields.io/github/watchers/forgepack/python-crud?style=social)](https://github.com/forgepack/python-crud)

__Made by [Forgepack](https://github.com/forgepack)__

</div>
