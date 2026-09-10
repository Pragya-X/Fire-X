"""Delivery contract tests; email is intercepted and never sent externally."""
from app.models import Notification
from app.services import notification_service as service


def test_notification_persists_and_emails_configured_recipients(db, monkeypatch):
    messages, broadcasts = [], []
    monkeypatch.setattr(service.settings, "MAIL_ALERT_RECIPIENTS", "one@example.invalid,two@example.invalid")
    monkeypatch.setattr(service, "broadcast", broadcasts.append)

    def capture_email(recipient, **payload):
        messages.append((recipient, payload))
        return {"delivered": False, "reason": "Intercepted by test"}

    monkeypatch.setattr(service.mailer, "send_alert_email", capture_email)
    results = service.notification_service.notify(
        db, title="Notification contract test", message="Test only", severity="warning",
        entity="test", entity_id="unit", to="acting@example.invalid", channels=["in-app", "email"],
    )
    note = db.get(Notification, results[0]["id"])
    assert note.message == "Test only"
    assert note.entity_id == "unit"
    assert broadcasts == [{"type": "notification", "data": results[0]}]
    assert [recipient for recipient, _ in messages] == ["one@example.invalid", "two@example.invalid"]
    assert all(payload["alert_url"].endswith("/alerts") for _, payload in messages)
    assert results[1]["to"] == [recipient for recipient, _ in messages]
    db.delete(note)
    db.commit()


def test_missing_recipient_and_sms_never_claim_delivery(db, monkeypatch):
    monkeypatch.setattr(service.settings, "MAIL_ALERT_RECIPIENTS", "")
    monkeypatch.setattr(service, "broadcast", lambda payload: None)

    def unexpected_email(*args, **kwargs):
        raise AssertionError("No email should be attempted without a recipient")

    monkeypatch.setattr(service.mailer, "send_alert_email", unexpected_email)
    results = service.notification_service.notify(db, title="Test only", message="Test only", channels=["email", "sms"])
    assert len(results) == 2
    assert all(result["delivered"] is False for result in results)
    assert results[1]["reason"] == "No SMS provider configured"
