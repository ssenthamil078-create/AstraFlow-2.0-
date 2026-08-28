"""
Phase 2 — Database engine and session management.

Phase 3 note: `init_db()` now also registers the Phase 3 `documents` table
(app/models/document.py) alongside Phase 2's `financial_events` table.

Phase 5 note: `init_db()` now also registers `income_sources` and
`income_payment_observations` (app/models/income_source.py,
app/models/income_payment_observation.py).

Phase 6 note: `init_db()` now also registers `users` (app/models/user.py).

Defaults to a local SQLite file so Phase 2 has zero external dependencies
(matches the spec's "Option A: fully local" build). Swapping to Supabase/
Postgres later is a one-line env var change — no application code changes,
because everything above this module talks to SQLAlchemy sessions, not to
SQLite or Postgres specifically.
"""

import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.environ.get("ASTRAFLOW_DATABASE_URL", "sqlite:///./astraflow.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Shared declarative base for every ORM model in the project."""


def init_db() -> None:
    """Create all tables. Fine for a hackathon build; a real deployment
    would use Alembic migrations instead of create_all — deferred, since
    it isn't needed until the schema needs versioned migrations in
    production (roadmap Phase 11)."""
    from app.models import (  # noqa: F401  (ensures models are registered)
        document,
        financial_event,
        financial_state_snapshot,
        goal,
        income_payment_observation,
        income_source,
        user,
    )

    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    """Context-managed session for scripts/services. FastAPI routers
    (Phase 3+) will use a request-scoped dependency instead, but that
    dependency wraps this same SessionLocal."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
