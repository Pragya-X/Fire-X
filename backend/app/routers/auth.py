from __future__ import annotations

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, hash_password, require_role, verify_password
from app.config import settings
from app.database import get_db
from app.models import ActivityLog, User
from app.schemas import (
    ChangePasswordRequest,
    CreateUserRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    ResetPasswordRequest,
    UserOut,
)
from app.services import mailer
from app.services.google_auth import (
    build_authorize_url,
    fetch_userinfo,
    google_configured,
    upsert_google_user,
)

RESET_TOKEN_MINUTES = 30

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    db.add(ActivityLog(user=user.email, action="login", entity="auth", details={"role": user.role, "provider": "password"}))
    db.commit()
    return LoginResponse(access_token=create_access_token(user), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.get("/google/login")
def google_login():
    """Start Google sign-in.

    When credentials are configured, returns the Google consent URL and the
    frontend redirects the browser there. Without credentials it returns
    ``configured: false`` so the UI can offer the labeled demo SSO flow.
    """
    if not google_configured():
        return {
            "configured": False,
            "authorize_url": None,
            "message": "Google SSO is not configured on this server - demo Google sign-in is available instead.",
        }
    return {
        "configured": True,
        "authorize_url": build_authorize_url(secrets.token_urlsafe(16)),
        "message": "",
    }


@router.get("/google/callback")
def google_callback(code: str, state: Optional[str] = None, db: Session = Depends(get_db)):
    """OAuth callback: exchange the code, upsert the user and redirect back to the frontend with a JWT."""
    if not google_configured():
        raise HTTPException(status_code=400, detail="Google SSO is not configured on this server")
    try:
        info = fetch_userinfo(code)
    except Exception as exc:  # network / provider errors
        raise HTTPException(status_code=502, detail=f"Google sign-in failed: {exc}")
    email = info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google account has no verified email")
    user = upsert_google_user(db, email, info.get("name") or email.split("@")[0])
    token = create_access_token(user)
    db.add(ActivityLog(user=user.email, action="login", entity="auth", details={"provider": "google", "role": user.role}))
    db.commit()
    # Token is passed via query param for the SPA flow; acceptable for this deployment.
    redirect_url = f"{settings.FRONTEND_URL.rstrip('/')}/login?token={token}"
    return RedirectResponse(url=redirect_url, status_code=302)


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the signed-in user's password after verifying the current one."""
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    user.password_hash = hash_password(body.new_password)
    db.add(ActivityLog(user=user.email, action="password_change", entity="auth", details={}))
    db.commit()
    mailer.send_password_changed_email(user.email, user.name)
    return {"ok": True}


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send a password-reset link to the account's email.

    Always returns 200 so the endpoint cannot be used to probe which emails
    have accounts. Without SMTP configured the email lands in the mail outbox
    (console fallback) so the demo flow still works.
    """
    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if user is not None:
        token = jwt.encode(
            {
                "purpose": "password_reset",
                "password_fingerprint": hashlib.sha256(user.password_hash.encode()).hexdigest(),
                "sub": str(user.id),
                "exp": datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_MINUTES),
                "iat": datetime.now(timezone.utc),
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"
        mailer.send_password_reset_email(user.email, user.name, reset_url)
        db.add(ActivityLog(user=user.email, action="password_reset_requested", entity="auth", details={"outcome": "link_sent"}))
        db.commit()
    else:
        # Behave identically for unknown accounts to avoid user enumeration.
        mailer.send_password_reset_email(
            body.email.strip().lower(),
            "there",
            f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token=invalid",
        )
    return {"ok": True}


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Set a new password using a reset token (single use)."""
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    try:
        payload = jwt.decode(body.token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Reset link expired - request a new one")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid reset link")
    if payload.get("purpose") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid reset link")
    try:
        user_id = int(payload.get("sub", 0))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid reset link")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid reset link")
    fingerprint = hashlib.sha256(user.password_hash.encode()).hexdigest()
    if not hmac.compare_digest(str(payload.get("password_fingerprint", "")), fingerprint):
        raise HTTPException(status_code=400, detail="Reset link already used or superseded")
    user.password_hash = hash_password(body.new_password)
    db.add(ActivityLog(user=user.email, action="password_reset", entity="auth", details={}))
    db.commit()
    mailer.send_password_changed_email(user.email, user.name)
    return {"ok": True}


@router.post("/users", response_model=UserOut)
def create_user(body: CreateUserRequest, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    """Admin-only: create an account and email the welcome link."""
    email = body.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user = User(
        email=email,
        name=body.name.strip(),
        password_hash=hash_password(body.password),
        role=body.role if body.role in ("viewer", "field", "analyst", "admin") else "viewer",
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(ActivityLog(user=admin.email, action="user_created", entity="user", entity_id=str(user.id), details={"email": email, "role": user.role}))
    db.commit()
    db.refresh(user)
    mailer.send_welcome_email(user.email, user.name)
    return UserOut.model_validate(user)


# ---- Admin: user management ----

@router.get("/users", response_model=list[UserOut])
def list_users(admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    """Admin-only: list all users."""
    return [UserOut.model_validate(u) for u in db.query(User).order_by(User.id).all()]


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UpdateUserRequest,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Admin-only: update a user's role, name or active status."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    changes: dict = {}
    if body.role is not None:
        if body.role not in ("viewer", "field", "analyst", "admin"):
            raise HTTPException(status_code=400, detail="Invalid role")
        if user_id == admin.id and body.role != "admin":
            raise HTTPException(status_code=400, detail="Cannot demote your own admin account")
        changes["role"] = body.role
        user.role = body.role
    if body.is_active is not None:
        if user_id == admin.id and not body.is_active:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        changes["is_active"] = body.is_active
        user.is_active = body.is_active
    if body.name is not None:
        changes["name"] = body.name
        user.name = body.name.strip()
    db.add(ActivityLog(user=admin.email, action="user_updated", entity="user", entity_id=str(user_id), details=changes))
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Admin-only: permanently delete a user."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.add(ActivityLog(user=admin.email, action="user_deleted", entity="user", entity_id=str(user_id), details={"email": user.email}))
    db.delete(user)
    db.commit()
    return {"ok": True}