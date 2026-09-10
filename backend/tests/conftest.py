from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

# Make app importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def pytest_configure(config):
    """Isolate settings before test modules import the app or seed a database."""
    sandbox = tempfile.TemporaryDirectory(prefix="firex-tests-")
    folder = Path(sandbox.name)
    environment = pytest.MonkeyPatch()
    values = {
        "ENV": "test", "DEBUG": "false", "DEMO_MODE": "true",
        "DATABASE_URL": "sqlite:///" + str(folder / "test_firex.db"),
        "DATA_DIR": str(folder / "data"), "MODEL_DIR": str(folder / "models"),
        "UPLOAD_DIR": str(folder / "uploads"), "ML_MODE": "rules",
        "ML_FALLBACK_MODE": "rules", "EVENT_MODEL_PATH": "", "REFERENCE_BUNDLE_PATH": "",
        "JWT_SECRET": "isolated-test-only-01234567890123456789", "CORS_ORIGINS": "*",
        "SMTP_HOST": "", "SMTP_USER": "", "SMTP_PASSWORD": "", "MAIL_ALERT_RECIPIENTS": "",
        "FIRMS_API_KEY": "", "FIRMS_MAP_KEY": "", "SATELLITE_API_KEY": "",
        "OPENAI_API_KEY": "", "GOOGLE_CLIENT_ID": "", "GOOGLE_CLIENT_SECRET": "",
    }
    for key, value in values.items():
        environment.setenv(key, value)

    def cleanup():
        environment.undo()
        sandbox.cleanup()

    config.add_cleanup(cleanup)


@pytest.fixture(scope="session")
def db_engine():
    from app.database import engine, init_db

    init_db()
    yield engine


@pytest.fixture()
def db(db_engine):
    from app.database import SessionLocal

    session = SessionLocal()
    yield session
    session.rollback()
    session.close()
