<div align="center">

# _Python CRUD_

[![GitHub stars](https://img.shields.io/github/stars/forgepack/python-crud?style=social)](https://github.com/forgepack/python-crud)
[![GitHub forks](https://img.shields.io/github/forks/forgepack/python-crud?style=social)](https://github.com/forgepack/python-crud/fork)
[![GitHub watchers](https://img.shields.io/github/watchers/forgepack/python-crud?style=social)](https://github.com/forgepack/python-crud)

[![CI](https://github.com/forgepack/python-crud/actions/workflows/ci.yml/badge.svg)](https://github.com/forgepack/python-crud/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/forgepack/python-crud/blob/main/LICENSE.md)

</div>

Production-ready FastAPI core boilerplate featuring **JWT Authentication**, **Refresh Token Rotation & Blacklist**, **Granular RBAC (Roles & Permissions)**, **Brute-Force Lockout**, **Audit Trails**, **Soft Delete**, and **Optimistic Concurrency Control**.

Designed as a foundational platform to plug in modular Python services and microservices under a unified authentication and authorization layer.

---

## Tech Stack

![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)

---

## Key Features

- **Authentication & Session Security:** PBKDF2-HMAC-SHA256 password hashing (600,000 iterations), JWT access/refresh tokens with `jti` tracking, automatic refresh token rotation, token revocation blacklist, and account lockout after 5 consecutive failed login attempts.
- **Role-Based Access Control (RBAC):** Fine-grained permissions (`EnumPermissionAction`) synced automatically on startup, assignable to roles and users, with ownership checks (`SelfOrPermission`).
- **Enterprise Data Layer:** Generic `BaseRepository` and `SoftDeleteRepository` using SQLAlchemy 2.0, optimistic locking (`version_id`), and automatic audit fields (`created_by`, `updated_by`, `deleted_by`, timestamps).

---

## Endpoints

### Public & System Bootstrap
- `GET /` — Returns `{"message": "Hello, World!"}`.
- `GET /health` — Health check endpoint returning `{"status": "healthy"}`.
- `POST /admin/init/create-first-user` — Initializes the database with the first `admin` user and syncs all permissions (only works when the database has zero users; returns `409 Conflict` afterward).

### Authentication
- `POST /login` — Authenticates username or email and returns `access_token` and `refresh_token`.
- `POST /login/refresh` — Rotates the session by issuing a new token pair and revoking the used `refresh_token`.
- `POST /login/logout` — Revokes the provided `refresh_token` in the blacklist.

### Users (`/user` — Requires JWT Bearer Token)
- `POST /user` — Creates a new user *(requires `CREATE_USER` permission or `admin`)*.
- `GET /user` — Lists active users with pagination (`page`, `limit`).
- `GET /user/{user_id}` — Retrieves an active user *(owner or `READ_USER`)*.
- `PUT /user/{user_id}` — Updates an active user *(owner or `UPDATE_USER`)*.
- `DELETE /user/{user_id}` — Soft-deletes a user *(owner or `DELETE_USER`)*.
- `PATCH /user/{user_id}/restore` — Restores a soft-deleted user *(requires `admin`)*.
- `DELETE /user/{user_id}/hard` — Permanently deletes a user *(requires `admin`)*.
- `GET /user/{user_id}/security` — Returns lockout and failed login status *(requires `admin`)*.
- `PATCH /user/{user_id}/unlock` — Unlocks a locked account and resets failed attempts *(requires `admin`)*.

### Roles & Permissions (`/role`, `/permission` — Requires JWT Bearer Token)
- `POST /role`, `GET /role`, `GET /role/defaults`, `GET /role/{role_id}`, `PUT /role/{role_id}`, `DELETE /role/{role_id}`, `DELETE /role/{role_id}/hard`, `PATCH /role/{role_id}/restore` — Full Role lifecycle management.
- `PATCH /role/{role_id}/permissions` — Replaces permissions assigned to a role.
- `GET /permission`, `GET /permission/{permission_id}`, `GET /permission/by-action/{action}` — Read-only permission queries.
- `POST /permission/sync` — Manually syncs `EnumPermissionAction` values with the database *(requires `admin`)*.

---

## Configuration

Copy the environment template and configure your secrets:

### _Windows PowerShell_
```powershell
Copy-Item .env.example .env
```

### _Linux / macOS_
```bash
cp .env.example .env
```

Required and optional environment variables:
- `UVICORN_JWT_SECRET_KEY`: Secret key with **at least 32 characters** for signing access tokens.
- `UVICORN_JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Access token lifetime in minutes (default: `30`).
- `UVICORN_JWT_REFRESH_SECRET_KEY`: Optional separate secret key for refresh tokens (defaults to `UVICORN_JWT_SECRET_KEY`).
- `UVICORN_JWT_REFRESH_TOKEN_EXPIRE_MINUTES`: Refresh token lifetime in minutes (default: `10080` / 7 days).
- `UVICORN_DATABASE_URL`: SQLAlchemy database URL (default: `sqlite:///./app.db`).

---

## Development

This project requires **Python 3.13** or later.

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

# create alembic config
alembic init alembic

# delete file and directory if they exist
Remove-Item -Force -ErrorAction SilentlyContinue db.sqlite3, alembic\versions\*.py

# generates the initial migration file by comparing the models with the database
alembic revision --autogenerate -m "initial schema"

# apply the migration to the database
alembic upgrade head

# build wheel artifact
python -m build

# inspect the contents of the wheel
python -m zipfile -l dist/python_crud-1.0.0-py3-none-any.whl

# run application (*)
python -m app.main


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
