<div align="center">

# _Python Template_

[![GitHub stars](https://img.shields.io/github/stars/forgepack/python-template?style=social)](https://github.com/forgepack/python-template)
[![GitHub forks](https://img.shields.io/github/forks/forgepack/python-template?style=social)](https://github.com/forgepack/python-template/fork)
[![GitHub watchers](https://img.shields.io/github/watchers/forgepack/python-template?style=social)](https://github.com/forgepack/python-template)

[![CI](https://github.com/forgepack/python-template/actions/workflows/ci.yml/badge.svg)](https://github.com/forgepack/python-template/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/forgepack/python-template/blob/main/LICENSE.md)

</div>

Reusable Python application template built with FastAPI.

## Tech Stack

![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)

## Endpoints

- `GET /` returns `{"message": "Hello, World!"}`.
- `GET /health` returns `{"status": "healthy"}`.
- `POST /api/user` publicly registers a user with `username`, `email`, and `password`.
- `POST /api/login` publicly authenticates credentials and returns a JWT Bearer token.
- `GET /api/user` lists active users and requires a JWT Bearer token.
- `GET /api/user/{user_id}` retrieves an active user and requires a JWT Bearer token.
- `PUT /api/user/{user_id}` updates an active user and requires a JWT Bearer token.
- `DELETE /api/user/{user_id}` performs a soft delete and requires a JWT Bearer token.
- `PATCH /api/user/{user_id}/restore` restores a soft-deleted user and requires a JWT Bearer token.
- `DELETE /api/user/{user_id}/hard` permanently deletes a user and requires a JWT Bearer token.

Set `UVICORN_JWT_SECRET_KEY` to a secret of at least 32 characters before starting
the application. Tokens expire after 30 minutes by default; configure a different
value with `UVICORN_JWT_ACCESS_TOKEN_EXPIRE_MINUTES`.


## Configuration
### _Windows PowerShell_
```bash
Copy-Item .env.example .env
```
### _Linux_
```bash
cp .env.example .env
```

## Development

This project requires Python 3.13 or later.

```bash
# create virtual environment
# Windows PowerShell
py -3.13 -m venv .venv
# Linux
python3.13 -m venv .venv

# activate virtual environment (*)
# Windows PowerShell
.venv/Scripts/activate
# Linux
source .venv/bin/activate

# update pip
python -m pip install --upgrade pip

# install dependencies
python -m pip install -e ".[dev]"

# generate the artifacts
python -m build

# inspect the contents of the wheel
python -m zipfile -l dist/python_template-1.0.0-py3-none-any.whl

# run application (*)
python -m app.main

# concat
py -3.13 -m venv .venv; .venv\Scripts\Activate.ps1; python -m pip install --upgrade pip; python -m pip install -e ".[dev]"; python -m build; python -m zipfile -l dist/python_template-1.0.0-py3-none-any.whl; python -m app.main
```

## Ruff linter formatting

```bash
# automatically formats the code to follow the standard
python -m ruff format .

# automatic correction
ruff check --fix .

# checks whether the code follows the formatting standard
python -m ruff format --check .

# identifies linting issues and potential code errors
python -m ruff check .

# concat:
python -m ruff format .; python -m ruff check --fix .; python -m ruff format --check .; python -m ruff check .
```

## Running Tests

```bash
# test coverage verification
python -m pytest --cov=app --cov-report=term-missing

# test report, in /htmlcov/index.html
python -m pytest --cov=app --cov-report=html

# test execution, with details
python -m pytest -v
```

## DEVELOPERS

### Contributors
> _[Gadelha TI](https://github.com/gadelhati)_ - *Research Software Engineer · Software Architect · Lead Developer*

## LICENSE

This project is licensed under the __MIT License__ - see the [MIT LICENSE](https://choosealicense.com/licenses/mit/) file for details.

<div align="center">

__⭐ Did you like the project? Leave a star! ⭐__

[![GitHub stars](https://img.shields.io/github/stars/forgepack/python-template?style=social)](https://github.com/forgepack/python-template)
[![GitHub forks](https://img.shields.io/github/forks/forgepack/python-template?style=social)](https://github.com/forgepack/python-template/fork)
[![GitHub watchers](https://img.shields.io/github/watchers/forgepack/python-template?style=social)](https://github.com/forgepack/python-template)

__Made by [Forgepack](https://github.com/forgepack)__

</div>