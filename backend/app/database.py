"""Database layer.

Works with SQLite out of the box (zero-config development fallback).
When ``DATABASE_URL`` points at PostgreSQL the same schema is used and the
PostGIS extension is enabled automatically when available.
"""
from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    url = settings.DATABASE_URL
    kwargs: dict = {"echo": False, "future": True}
    if url.startswith("sqlite"):
        # WAL lets readers run concurrently with the FIRMS ingest writer instead of
        # queueing behind its lock; busy_timeout avoids immediate 'database is locked'.
        kwargs["connect_args"] = {
            "check_same_thread": False,
            "timeout": 15,
        }
    engine = create_engine(url, **kwargs)

    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragmas(dbapi_conn, _record):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA busy_timeout=15000")
            cur.close()

    if settings.is_postgres:

        @event.listens_for(engine, "connect")
        def _enable_postgis(dbapi_conn, _record):  # pragma: no cover - optional
            try:
                cur = dbapi_conn.cursor()
                cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")
                cur.close()
                dbapi_conn.commit()
            except Exception:
                dbapi_conn.rollback()  # Leave connection usable; init_db reports extension errors.

    return engine


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Safe to call on every startup."""
    from app import event_models  # noqa: F401
    from app import models  # noqa: F401  (register models)

    Base.metadata.create_all(bind=engine)
    if settings.is_postgres:  # pragma: no cover
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))


def check_db() -> dict:
    """Return a small health report for the database."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        dialect = engine.dialect.name
        postgis = False
        if settings.is_postgres:
            with engine.connect() as conn:
                row = conn.execute(
                    text("SELECT PostGIS_Version()")
                ).fetchone()
                postgis = bool(row)
        return {"connected": True, "dialect": dialect, "postgis": postgis}
    except Exception as exc:  # pragma: no cover
        return {"connected": False, "error": str(exc)}