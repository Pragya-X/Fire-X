"""Email delivery.

- Live mode: SMTP (works with Gmail app passwords). Configured via
  ``SMTP_HOST`` / ``SMTP_PORT`` / ``SMTP_USER`` / ``SMTP_PASSWORD`` in ``.env``.
- Fallback mode (no SMTP): every email is written to ``data/outbox/*.eml`` and
  logged, so the demo still shows the full mail pipeline without credentials.

All send functions return ``{delivered, mode, to, subject}`` so callers can
surface the result in the UI.
"""
from __future__ import annotations

import logging
import smtplib
import uuid
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from app.config import settings

logger = logging.getLogger("firex.mailer")

OUTBOX_DIR = Path(settings.DATA_DIR) / "outbox"


def _outbox() -> Path:
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    return OUTBOX_DIR


def _build_message(to: str, subject: str, html: str, text: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.mail_from}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def send_email(to: str, subject: str, html: str, text: str) -> dict:
    if not settings.smtp_configured:
        # Console / outbox fallback - nothing leaves the machine.
        filename = _outbox() / f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}.eml"
        filename.write_text(f"To: {to}\nSubject: {subject}\n\n{text}\n\n[HTML version omitted in outbox]\n")
        logger.info("MAIL (console fallback) to=%s subject=%r outbox=%s", to, subject, filename)
        return {"delivered": False, "mode": "console", "to": to, "subject": subject, "outbox": str(filename)}

    try:
        msg = _build_message(to, subject, html, text)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            server.ehlo()
            if settings.SMTP_PORT == 587:
                server.starttls()
                server.ehlo()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("MAIL (smtp) to=%s subject=%r", to, subject)
        return {"delivered": True, "mode": "smtp", "to": to, "subject": subject}
    except Exception as exc:  # network / auth failures - never crash the request
        logger.warning("MAIL (smtp) to=%s failed: %s", to, exc)
        return {"delivered": False, "mode": "smtp-error", "to": to, "subject": subject, "error": str(exc)}


def _shell(subject: str, body: str, extra: str = "") -> tuple[str, str]:
    html = (
        "<div style='font-family:Arial,sans-serif;max-width:560px;margin:0 auto;"
        "border:1px solid #e2e8f0;border-radius:8px;overflow:hidden'>"
        "<div style='background:#0b1220;color:#fff;padding:16px 24px;font-weight:bold;letter-spacing:2px'>FIRE-X</div>"
        f"<div style='padding:24px;color:#1e293b;font-size:14px;line-height:1.6'>{body}</div>"
        "<div style='padding:12px 24px;background:#f8fafc;color:#64748b;font-size:11px'>"
        "Fire Intelligence &amp; Risk Evaluation Platform</div></div>"
    )
    text = f"FIRE-X\n{'=' * 40}\n\n{body}\n\nFire Intelligence & Risk Evaluation Platform{extra}\n"
    return html, text


def send_welcome_email(to: str, name: str, reset_link: str = "") -> dict:
    subject = "Welcome to FIRE-X"
    body = (
        f"<p>Hi {name},</p>"
        f"<p>Your FIRE-X account has been created with <b>{to}</b>.</p>"
        f"<p>Sign in at <a href='{settings.FRONTEND_URL}'>the FIRE-X command center</a> with your email and password.</p>"
        + (f"<p>Set a password you will remember via this one-time link: <a href='{reset_link}'>{reset_link}</a></p>" if reset_link else "")
        + "<p>If you did not expect this email, you can safely ignore it.</p>"
    )
    return send_email(to, subject, *_shell(subject, body))


def send_password_reset_email(to: str, name: str, reset_url: str) -> dict:
    subject = "FIRE-X password reset"
    body = (
        f"<p>Hi {name},</p>"
        f"<p>A password reset was requested for <b>{to}</b>. Use the link below to choose a new password. It expires in 30 minutes.</p>"
        f"<p><a href='{reset_url}' style='display:inline-block;background:#0284c7;color:#fff;padding:10px 18px;"
        f"border-radius:6px;text-decoration:none'>Reset password</a></p>"
        f"<p style='color:#64748b;font-size:12px'>Or paste this link: {reset_url}</p>"
        f"<p>If you did not request this, ignore this email - your password will not change.</p>"
    )
    return send_email(to, subject, *_shell(subject, body))


def send_password_changed_email(to: str, name: str) -> dict:
    subject = "FIRE-X password changed"
    body = f"<p>Hi {name},</p><p>Your FIRE-X password was just changed. If this was not you, contact your administrator immediately.</p>"
    return send_email(to, subject, *_shell(subject, body))


def send_alert_email(to: str, title: str, message: str, alert_url: str) -> dict:
    subject = f"FIRE-X alert: {title[:90]}"
    body = (
        f"<p style='color:#dc2626;font-weight:bold'>New FIRE-X alert</p>"
        f"<p><b>{title}</b></p>"
        f"<p>{message}</p>"
        f"<p><a href='{alert_url}' style='display:inline-block;background:#dc2626;color:#fff;padding:10px 18px;"
        f"border-radius:6px;text-decoration:none'>Open alert center</a></p>"
    )
    return send_email(to, subject, *_shell(subject, body))