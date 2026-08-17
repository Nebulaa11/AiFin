from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.db_models import User

security = HTTPBearer(auto_error=False)


def verify_google_token(token: str) -> dict:
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID in backend/.env",
        )
    try:
        return id_token.verify_oauth2_token(
            token, google_requests.Request(), settings.google_client_id
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}") from e


def create_access_token(user_id: int, email: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from e


def get_or_create_dev_user(db: Session, email: str, name: str) -> User:
    google_id = f"dev:{email}"
    user = db.query(User).filter(User.google_id == google_id).first()
    if user:
        user.name = name
        user.email = email
        db.commit()
        db.refresh(user)
        return user
    user = User(google_id=google_id, email=email, name=name, picture_url=None)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_user(db: Session, google_payload: dict) -> User:
    google_id = google_payload["sub"]
    user = db.query(User).filter(User.google_id == google_id).first()
    if user:
        user.email = google_payload.get("email", user.email)
        user.name = google_payload.get("name", user.name)
        user.picture_url = google_payload.get("picture")
        db.commit()
        db.refresh(user)
        return user
    user = User(
        google_id=google_id,
        email=google_payload.get("email", ""),
        name=google_payload.get("name", "User"),
        picture_url=google_payload.get("picture"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not creds or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(creds.credentials)
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
