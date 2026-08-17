import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import User, UserFinancialProfile
from app.models.schemas import UserProfile, UserProfileStore
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/user", tags=["user"])


def _default_profile() -> UserProfile:
    return UserProfile(
        age=28,
        income_monthly=80000,
        expenses_monthly=40000,
        savings=200000,
        loans=[],
        assets=[],
        risk_tolerance="medium",
        financial_goals=[],
        dependents=0,
    )


@router.get("/profile", response_model=UserProfileStore)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(UserFinancialProfile).filter(UserFinancialProfile.user_id == user.id).first()
    if not row or not row.profile_json or row.profile_json == "{}":
        return UserProfileStore(profile=_default_profile(), last_analysis=None)
    profile = UserProfile.model_validate_json(row.profile_json)
    analysis = json.loads(row.last_analysis_json) if row.last_analysis_json else None
    return UserProfileStore(profile=profile, last_analysis=analysis)


@router.put("/profile", response_model=UserProfileStore)
def save_profile(
    body: UserProfileStore,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(UserFinancialProfile).filter(UserFinancialProfile.user_id == user.id).first()
    if not row:
        row = UserFinancialProfile(user_id=user.id)
        db.add(row)
    row.profile_json = body.profile.model_dump_json()
    row.last_analysis_json = json.dumps(body.last_analysis) if body.last_analysis else None
    db.commit()
    db.refresh(row)
    return UserProfileStore(profile=body.profile, last_analysis=body.last_analysis)
