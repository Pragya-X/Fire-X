"""Google OAuth integration (server-side, optional).

Flow (when ``GOOGLE_CLIENT_ID`` / ``GOOGLE_CLIENT_SECRET`` are configured):

    GET /api/v1/auth/google/login   -> returns authorize URL
    user consents on accounts.google.com
    Google  ->  /api/v1/auth/google/callback?code=...  -> JWT -> redirect to frontend

When credentials are absent the endpoints are inert (``configured: false`` /
400) and the platform relies on email/password accounts.
"""
from __future__ import annotations

import base64
import hashlib
import secrets
import time
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import settings
from app.models import User

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_SCOPES = "openid email profile"

#: Role assigned to accounts created through Google sign-in.
DEFAULT_SSO_ROLE = "analyst"


def google_configured() -> bool:
    return bool(settings.GOOGLE_CLIENT_ID.strip() and settings.GOOGLE_CLIENT_SECRET.strip())


# ---- PKCE + CSRF state store -------------------------------------------------
# Pending authorizations live in-process for five minutes. The production
# deployment runs a single uvicorn worker; if the backend is ever scaled to
# multiple workers this must move to a shared store (e.g. the database).
_OAUTH_STATE_TTL = 300
_pending_states: dict[str, tuple[str, float]] = {}


def _pkce_pair() -> tuple[str, str]:
    """Return (verifier, challenge) using the S256 method."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def issue_authorization() -> tuple[str, str]:
    """Create a signed-off (state, authorize_url) pair with PKCE bound in.

    The verifier is kept server-side only; Google receives the matching
    S256 challenge and must echo the state back on the callback.
    """
    # Bound memory usage: drop the oldest entries past a sane ceiling.
    while len(_pending_states) >= 1000:
        oldest = min(_pending_states, key=lambda s: _pending_states[s][1])
        _pending_states.pop(oldest, None)
    now = time.monotonic()
    for s in [s for s, (_, t) in _pending_states.items() if now - t > _OAUTH_STATE_TTL]:
        _pending_states.pop(s, None)

    state = secrets.token_urlsafe(32)
    verifier, challenge = _pkce_pair()
    _pending_states[state] = (verifier, now)

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "access_type": "online",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "prompt": "select_account",
    }
    return state, f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def consume_state(state: str | None) -> str | None:
    """Return the PKCE verifier for a valid, unexpired state (single use)."""
    if not state:
        return None
    entry = _pending_states.pop(state, None)
    if entry is None:
        return None
    verifier, created = entry
    if time.monotonic() - created > _OAUTH_STATE_TTL:
        return None
    return verifier


def fetch_userinfo(code: str, code_verifier: str) -> dict:
    """Exchange the authorization code (PKCE-bound) and fetch the profile."""
    with httpx.Client(timeout=15) as client:
        token_resp = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
                "code_verifier": code_verifier,
            },
        )
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise ValueError("Google token exchange returned no access_token")
        info_resp = client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        info_resp.raise_for_status()
        return info_resp.json()


def upsert_google_user(db: Session, email: str, name: str) -> User:
    """Find an existing account by email or create one for the Google profile."""
    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        # OAuth-only accounts get an unverifiable random hash so password login can never succeed.
        user = User(
            email=email,
            name=name or email.split("@")[0],
            password_hash=hash_password(secrets.token_hex(24)),
            role=DEFAULT_SSO_ROLE,
            is_active=True,
        )
        db.add(user)
        db.flush()
        from app.services import mailer

        mailer.send_welcome_email(user.email, user.name)
    else:
        user.name = name or user.name
        if not user.is_active:
            user.is_active = True
    db.commit()
    db.refresh(user)
    return user