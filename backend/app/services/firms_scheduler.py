"""Background FIRMS sync scheduler.

Runs the FIRMS ingest on a fixed interval server-side so the data stays fresh
regardless of whether anyone has the dashboard open. Previously the frontend
triggered an ingest on every dashboard visit, which blocked SQLite writes
against reads and made the whole app feel slow.
"""
from __future__ import annotations

import logging
import threading
import time

from app.config import settings

logger = logging.getLogger("firex")

INTERVAL_SECONDS = max(120, settings.FIRMS_SYNC_INTERVAL)  # floor at 2 minutes
_sync_lock = threading.Lock()
_stop_event = threading.Event()
_thread: threading.Thread | None = None


def run_firms_sync() -> dict | None:
    """Run one FIRMS ingest cycle in its own DB session.

    Returns the ingest result dict, or None when skipped/failed. Safe to call
    from the scheduler thread and from the manual sync endpoint concurrently -
    the lock collapses overlapping runs into a no-op.
    """
    if not _sync_lock.acquire(blocking=False):
        logger.info("FIRMS sync already running; skipping overlapping trigger")
        return None
    try:
        from app.database import SessionLocal
        from app.models import User
        from app.routers.ingest import ingest_firms
        from app.auth import require_role

        db = SessionLocal()
        try:
            # ingest_firms requires an analyst user for the activity log;
            # use the seeded admin as the system actor.
            system_user = db.query(User).filter(User.role == "admin").first()
            if system_user is None:
                logger.warning("FIRMS sync skipped: no admin user found")
                return None
            result = ingest_firms(user=system_user, db=db)
            logger.info(
                "FIRMS sync complete: created=%s updated=%s alerts=%s",
                result.get("created"), result.get("updated"), result.get("alerts_created"),
            )
            return result
        finally:
            db.close()
    except Exception:
        logger.exception("FIRMS sync failed")
        return None
    finally:
        _sync_lock.release()


def _loop() -> None:
    # Small initial delay so app startup and first requests are not delayed.
    _stop_event.wait(15)
    while not _stop_event.is_set():
        started = time.monotonic()
        run_firms_sync()
        # Sleep the remainder of the interval regardless of how long the sync took.
        elapsed = time.monotonic() - started
        _stop_event.wait(max(5.0, INTERVAL_SECONDS - elapsed))


def start_scheduler() -> None:
    global _thread
    if settings.ENV == "production" and not settings.FIRMS_AUTO_SYNC:
        logger.info("FIRMS auto-sync disabled in production")
        return
    if _thread is not None and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(target=_loop, name="firms-sync", daemon=True)
    _thread.start()
    logger.info("FIRMS auto-sync scheduler started (every %ss)", INTERVAL_SECONDS)


def stop_scheduler() -> None:
    _stop_event.set()
