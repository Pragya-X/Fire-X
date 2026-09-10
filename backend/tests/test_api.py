from fastapi.testclient import TestClient

from app.main import app
from app.seed import main as seed_main

client = TestClient(app)


def setup_module():
    seed_main()


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_activity_route_preserves_filter_and_shape():
    r = client.get("/api/v1/activity", params={"limit": 2})
    assert r.status_code == 200
    assert r.json()["total"] == len(r.json()["items"]) <= 2
    filtered = client.get("/api/v1/activity", params={"action": "nonexistent-test-action"})
    assert filtered.json() == {"items": [], "total": 0}


def test_missing_firms_never_inserts_demo_when_disabled(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "FIRMS_API_KEY", "")
    monkeypatch.setattr(settings, "FIRMS_MAP_KEY", "")
    token = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).json()["access_token"]
    before = client.get("/api/v1/hotspots").json()["total"]
    result = client.post("/api/v1/ingest/firms", headers={"Authorization": f"Bearer {token}"})
    assert result.status_code == 503
    assert "demo fallback is disabled" in result.json()["detail"]
    assert client.get("/api/v1/hotspots").json()["total"] == before


ADMIN_EMAIL = "npgearly@gmail.com"
ADMIN_PASSWORD = "admin123"


def test_disabling_demo_blocks_all_demo_actions_without_writes(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "DEMO_MODE", False)
    before = client.get("/api/v1/hotspots").json()["total"]
    for method, path in [("POST", "/ingest/demo"), ("POST", "/ingest/landcover"),
                         ("POST", "/scenario/run"), ("GET", "/scenario/state")]:
        response = client.request(method, "/api/v1" + path)
        assert response.status_code == 404
        assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert client.get("/api/v1/hotspots").json()["total"] == before


def test_login_ok():
    r = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200
    assert r.json()["access_token"]
    assert r.json()["user"]["role"] == "admin"
    assert r.json()["user"]["created_at"]


def test_login_bad_password():
    r = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"})
    assert r.status_code == 401


def test_change_password():
    token = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # wrong current password rejected
    r = client.post("/api/v1/auth/change-password", headers=headers, json={"current_password": "nope", "new_password": "newpass123"})
    assert r.status_code == 401
    # too-short new password rejected
    r = client.post("/api/v1/auth/change-password", headers=headers, json={"current_password": ADMIN_PASSWORD, "new_password": "123"})
    assert r.status_code == 400
    # valid change
    r = client.post("/api/v1/auth/change-password", headers=headers, json={"current_password": ADMIN_PASSWORD, "new_password": "newpass123"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    # old password no longer works
    assert client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).status_code == 401
    # new password works
    assert client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": "newpass123"}).status_code == 200
    # restore the seeded password so other tests keep passing
    token2 = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": "newpass123"}).json()["access_token"]
    client.post("/api/v1/auth/change-password", headers={"Authorization": f"Bearer {token2}"}, json={"current_password": "newpass123", "new_password": ADMIN_PASSWORD})


def test_hotspots_list():
    r = client.get("/api/v1/hotspots", params={"page_size": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 300
    assert len(body["items"]) == 5


def test_hotspots_filter():
    r = client.get("/api/v1/hotspots", params={"classification": "Wildfire"})
    assert r.status_code == 200
    assert all(i["classification"] == "Wildfire" for i in r.json()["items"])


def test_hotspot_detail():
    r = client.get("/api/v1/hotspots/1")
    assert r.status_code == 200
    body = r.json()
    assert body["code"].startswith("HX-")
    assert "features" in body
    assert "history" in body


def test_hotspot_geojson():
    r = client.get("/api/v1/hotspots/geojson")
    assert r.status_code == 200
    fc = r.json()
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) >= 300


def test_infrastructure_geojson():
    r = client.get("/api/v1/infrastructure/geojson")
    assert r.status_code == 200
    assert len(r.json()["features"]) > 50


def test_network_geojson():
    r = client.get("/api/v1/infrastructure/network/geojson")
    assert r.status_code == 200
    assert r.json()["type"] == "FeatureCollection"
    assert len(r.json()["features"]) > 0


def test_landcover_geojson():
    r = client.get("/api/v1/infrastructure/landcover/geojson")
    assert r.status_code == 200
    assert r.json()["type"] == "FeatureCollection"
    assert len(r.json()["features"]) > 0


def test_industrial_zones():
    r = client.get("/api/v1/industrial-zones")
    assert r.status_code == 200
    assert r.json()["total"] >= 20


def test_alerts_flow():
    token = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/api/v1/alerts", headers=headers)
    assert r.status_code == 200
    alerts = r.json()["items"]
    assert len(alerts) > 0
    aid = alerts[0]["id"]
    r = client.post(f"/api/v1/alerts/{aid}/acknowledge", headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "acknowledged"
    r = client.post(f"/api/v1/alerts/{aid}/escalate", headers=headers)
    assert r.json()["status"] == "escalated"
    r = client.post(f"/api/v1/alerts/{aid}/resolve", headers=headers)
    assert r.json()["status"] == "resolved"


def test_alerts_require_auth():
    r = client.post("/api/v1/alerts/1/acknowledge")
    assert r.status_code == 401


def test_analytics():
    r = client.get("/api/v1/analytics")
    assert r.status_code == 200
    body = r.json()
    assert len(body["by_classification"]) == 6
    assert len(body["daily"]) > 0
    assert "avg_classification_confidence" in body


def test_ml_classify():
    assert client.post("/api/v1/ml/classify", json={"hotspot_id": 1}).status_code == 401
    token = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).json()["access_token"]
    r = client.post("/api/v1/ml/classify", json={"hotspot_id": 1}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["classification"]
    assert 0 <= body["confidence"] <= 1
    assert len(body["probabilities"]) == 6
    assert body["feature_importance"]


def test_ingest_demo():
    token = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).json()["access_token"]
    r = client.post("/api/v1/ingest/demo", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "demo"
    assert body["records_received"] > 0
    # repeat run must not violate the unique feature constraint
    r2 = client.post("/api/v1/ingest/demo", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200


def test_historical():
    r = client.get("/api/v1/historical", params={"page_size": 5})
    assert r.status_code == 200
    assert r.json()["total"] >= 300


def test_system_health():
    r = client.get("/api/v1/system-health")
    assert r.status_code == 200
    assert len(r.json()["components"]) >= 8


def test_copilot_demo_mode():
    r = client.post("/api/v1/copilot/ask", json={"question": "How many wildfires were detected this week?"})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "demo"
    assert "wildfire" in body["answer"].lower()


def test_demo_scenario():
    token = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).json()["access_token"]
    r = client.post("/api/v1/scenario/run", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["completed"] is True
    assert body["hotspot"]["classification"] == "Industrial Fire"
    assert body["hotspot"]["risk_level"] == "CRITICAL"
    assert body["alert"]["severity"] == "CRITICAL"
    assert len(body["steps"]) == 5


def test_export_csv():
    r = client.get("/api/v1/hotspots/export", params={"format": "csv"})
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "HX-" in r.text


def test_export_pdf():
    r = client.get("/api/v1/hotspots/1/report")
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"


def test_mailer_console_fallback():
    from app.services import mailer

    res = mailer.send_password_reset_email("nobody@example.com", "Nobody", "http://localhost:3000/reset-password?token=xyz")
    assert res["mode"] == "console"
    assert res["delivered"] is False
    assert res["outbox"]
    assert "FIRE-X password reset" in res["subject"]


def test_forgot_and_reset_password():
    from pathlib import Path

    from app.config import settings
    from app.services import mailer

    outbox = Path(mailer.OUTBOX_DIR)
    before = set(outbox.glob("*.eml")) if outbox.exists() else set()

    r = client.post("/api/v1/auth/forgot-password", json={"email": ADMIN_EMAIL})
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # Find the reset email in the console outbox
    new_files = [f for f in outbox.glob("*.eml") if f not in before]
    reset_mail = next((f for f in new_files if "password reset" in f.read_text().lower()), None)
    assert reset_mail is not None
    import re

    content = reset_mail.read_text()
    match = re.search(r"reset-password\?token=([A-Za-z0-9_.-]+)", content)
    assert match is not None
    token = match.group(1)
    assert token and token != "invalid"

    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    # Reset with the token
    r = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "reset12345"})
    assert r.status_code == 200
    assert client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "replay12345"}).status_code == 400
    # Old password dead, new one works
    assert client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": "reset12345"}).status_code == 200
    # Invalid token rejected
    r = client.post("/api/v1/auth/reset-password", json={"token": "garbage", "new_password": "reset12345"})
    assert r.status_code == 400
    # Restore the seeded password
    token2 = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": "reset12345"}).json()["access_token"]
    r = client.post("/api/v1/auth/change-password", headers={"Authorization": f"Bearer {token2}"}, json={"current_password": "reset12345", "new_password": ADMIN_PASSWORD})
    assert r.status_code == 200


def test_admin_create_user():
    token = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/v1/auth/users", headers=headers, json={"name": "New Officer", "email": "new.officer@firex.test", "password": "pass1234", "role": "field"})
    assert r.status_code == 200
    assert r.json()["email"] == "new.officer@firex.test"
    assert r.json()["role"] == "field"
    # New account can log in
    assert client.post("/api/v1/auth/login", json={"email": "new.officer@firex.test", "password": "pass1234"}).status_code == 200
    # Duplicate rejected
    r = client.post("/api/v1/auth/users", headers=headers, json={"name": "Again", "email": "new.officer@firex.test", "password": "pass1234", "role": "viewer"})
    assert r.status_code == 409
    # Non-admin forbidden
    r = client.post("/api/v1/auth/users", json={"name": "X", "email": "x@firex.test", "password": "pass1234", "role": "viewer"})
    assert r.status_code == 401


def test_notifications_scope_and_read():
    token = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v1/alerts/notifications", headers=headers)
    assert r.status_code == 200
    before = r.json()["unread"]

    # Running the scenario creates a user-scoped notification
    r = client.post("/api/v1/scenario/run", headers=headers)
    assert r.status_code == 200

    r = client.get("/api/v1/alerts/notifications", headers=headers)
    body = r.json()
    assert body["unread"] > before
    assert any(n["title"] == "Industrial Fire Escalation Scenario" for n in body["items"])

    # Mark a single notification read
    target = next(n for n in body["items"] if n["title"] == "Industrial Fire Escalation Scenario")
    r = client.post(f"/api/v1/alerts/notifications/{target['id']}/read", headers=headers)
    assert r.status_code == 200
    r = client.get("/api/v1/alerts/notifications", headers=headers)
    assert r.json()["unread"] == body["unread"] - 1

    # Mark all read
    r = client.post("/api/v1/alerts/notifications/mark-read", headers=headers)
    assert r.status_code == 200
    r = client.get("/api/v1/alerts/notifications", headers=headers)
    assert r.json()["unread"] == 0


def test_google_login_status():
    r = client.get("/api/v1/auth/google/login")
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is False
    assert body["authorize_url"] is None


def test_google_callback_rejected_without_config():
    r = client.get("/api/v1/auth/google/callback", params={"code": "abc"})
    assert r.status_code == 400




def test_model_provenance_contract():
    health=client.get('/api/v1/ml/status').json()
    assert health['model_mode']=='RULES'
    assert health['training_data_type']=='none'
    assert health['evaluation_available'] is False
    token=client.post('/api/v1/auth/login',json={'email':ADMIN_EMAIL,'password':ADMIN_PASSWORD}).json()['access_token']
    result=client.post('/api/v1/ml/classify',json={'hotspot_id':1},headers={'Authorization':f'Bearer {token}'}).json()
    assert result['model_mode']=='RULES' and result['model_version']
    assert result['explanation']['factor_type']=='heuristic_context'
    detail=client.get('/api/v1/hotspots/1').json()
    assert detail['explanation']['model_mode']=='RULES'
