import pytest
from app.config import Settings


def test_production_rejects_defaults():
    with pytest.raises(ValueError,match='Unsafe production configuration'):
        Settings(_env_file=None,ENV='production')


def production(**overrides):
    values=dict(_env_file=None,ENV='production',DEBUG=False,DEMO_MODE=False,JWT_SECRET='unit-test-only-not-a-real-secret-0123456789',
        DATABASE_URL='postgresql://test@db/test',CORS_ORIGINS='https://test.invalid',GOOGLE_CLIENT_ID='',GOOGLE_CLIENT_SECRET='')
    values.update(overrides)
    return Settings(**values)


def test_production_valid_explicit_config():
    assert production().ENV=='production'

@pytest.mark.parametrize('overrides',[{'CORS_ORIGINS':'*'},{'DEMO_MODE':True},{'DEBUG':True},{'JWT_SECRET':'short'},
    {'DATABASE_URL':'sqlite:///test.db'},{'GOOGLE_CLIENT_ID':'id-without-secret'},
    {'GOOGLE_CLIENT_ID':'id','GOOGLE_CLIENT_SECRET':'secret','GOOGLE_REDIRECT_URI':'http://localhost:8000/api/v1/auth/google/callback'}])
def test_production_guards(overrides):
    with pytest.raises(ValueError):production(**overrides)


def test_production_allows_hardened_google_oauth():
    s = production(GOOGLE_CLIENT_ID='id', GOOGLE_CLIENT_SECRET='secret',
                   GOOGLE_REDIRECT_URI='https://firex.example.com/api/v1/auth/google/callback')
    assert s.ENV == 'production'


@pytest.mark.parametrize("demo,key", [(False, ""), (False, "test-key"), (True, "test-key")])
def test_remote_landcover_is_unavailable_not_live(monkeypatch, demo, key):
    from app.config import settings
    from app.providers.firms import ProviderUnavailable
    from app.providers.landcover import get_landcover_provider

    monkeypatch.setattr(settings, "DEMO_MODE", demo)
    monkeypatch.setattr(settings, "SATELLITE_API_KEY", key)
    provider = get_landcover_provider()
    assert provider.mode == "unavailable"
    with pytest.raises(ProviderUnavailable):
        provider.fetch()


@pytest.mark.parametrize("demo", [False, True])
def test_demo_routes_match_startup_mode(tmp_path, demo):
    """A fresh process checks registration, not just a mocked runtime setting."""
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    environment = dict(os.environ, DEMO_MODE=str(demo).lower(),
                       DATABASE_URL="sqlite://", DATA_DIR=str(tmp_path),
                       UPLOAD_DIR=str(tmp_path), MODEL_DIR=str(tmp_path))
    result = subprocess.run(
        [sys.executable, "-c", "from app.main import app; import json; print(json.dumps(list(app.openapi()['paths'])))"],
        cwd=Path(__file__).resolve().parents[1], env=environment,
        capture_output=True, text=True, check=True,
    )
    paths = json.loads(result.stdout)
    for path in ["/api/v1/ingest/demo", "/api/v1/ingest/landcover",
                 "/api/v1/scenario/run", "/api/v1/scenario/state"]:
        assert (path in paths) is demo
    assert "/api/v1/ingest/firms" in paths
    assert "/api/v1/thermal-events" in paths
