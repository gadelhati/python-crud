import os

from sqlalchemy.engine import make_url

os.environ.setdefault(
    "UVICORN_DATABASE_URL",
    "sqlite:///./db_test.sqlite3",
)

test_database_url = make_url(os.environ["UVICORN_DATABASE_URL"])

if test_database_url.get_backend_name() not in {"sqlite", "postgresql"}:
    raise RuntimeError("Unsupported test database")

if test_database_url.get_backend_name() == "postgresql" and (
    test_database_url.database != "app_test"
    or test_database_url.host not in {"localhost", "127.0.0.1"}
):
    raise RuntimeError("Tests can only run against the dedicated local PostgreSQL test database")
