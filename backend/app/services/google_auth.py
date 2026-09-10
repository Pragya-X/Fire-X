"""Google OAuth integration (server-side, optional).

Flow (when ``GOOGLE_CLIENT_ID`` / ``GOOGLE_CLIENT_SECRET`` are configured):

    GET /api/v1/auth/google/login   -> returns authorize URL
    user consents on accounts.google.com
    Google  ->  /api/v1/auth/google/callback?code=...  -> JWT -> redirect to frontend

When credentials are absent the endpoints are inert (``configured: false`` /
400) and the platform relies on email/password accounts.
"""
from __future__ import annotations

import secrets
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


def build_authorize_url(state: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "access_type": "online",
        "state": state,
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def fetch_userinfo(code: str) -> dict:
    """Exchange the authorization code for an access token and fetch the profile."""
    with httpx.Client(timeout=15) as client:
        token_resp = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
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