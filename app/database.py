# app/database.py
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///db.sqlite3"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def initialize_database() -> None:
    """Creates the development schema and resets incompatible user schemas."""
    Base.metadata.create_all(bind=engine)

    if engine.dialect.name != "sqlite":
        return

    columns = {column["name"] for column in inspect(engine).get_columns("users")}
    required_columns = {"username", "email", "password_hash", "deleted_at"}
    if not required_columns.issubset(columns):
        with engine.begin() as connection:
            connection.execute(text("DROP TABLE users"))
        Base.metadata.create_all(bind=engine)


def get_db():
    with SessionLocal() as db:
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
