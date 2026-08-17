from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.schemas import AuthTokenResponse, AuthUserResponse, GoogleAuthRequest
from app.services.auth import (
    create_access_token,
    get_current_user,
    get_or_create_dev_user,
    get_or_create_user,
    verify_google_token,
)
from app.models.db_models import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/config")
def auth_config():
    settings = get_settings()
    return {
        "google_client_id": settings.google_client_id,
        "google_configured": bool(settings.google_client_id),
        "dev_auth_enabled": settings.dev_auth_enabled,
    }


@router.post("/dev-login", response_model=AuthTokenResponse)
def dev_login(db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.dev_auth_enabled:
        raise HTTPException(
            status_code=403,
            detail="Dev login disabled. Set GOOGLE_CLIENT_ID or ALLOW_DEV_AUTH=true.",
        )
    user = get_or_create_dev_user(db, "dev@local.aifin", "Local Dev User")
    token = create_access_token(user.id, user.email)
    return AuthTokenResponse(
        access_token=token,
        user=AuthUserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            picture_url=user.picture_url,
        ),
    )


@router.post("/google", response_model=AuthTokenResponse)
def google_login(body: GoogleAuthRequest, db: Session = Depends(get_db)):
    payload = verify_google_token(body.id_token)
    user = get_or_create_user(db, payload)
    token = create_access_token(user.id, user.email)
    return AuthTokenResponse(
        access_token=token,
        user=AuthUserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            picture_url=user.picture_url,
        ),
    )


@router.get("/me", response_model=AuthUserResponse)
def me(user: User = Depends(get_current_user)):
    return AuthUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture_url=user.picture_url,
    )
