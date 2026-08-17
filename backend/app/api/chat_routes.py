import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import ChatMessage, ChatSession, User, UserFinancialProfile
from app.models.schemas import (
    ChatMessageResponse,
    ChatSendRequest,
    ChatSendResponse,
    ChatSessionResponse,
    UserProfile,
)
from app.services.ai_advisor import AIAdvisor
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
_advisor = AIAdvisor()


def _session_response(session: ChatSession) -> ChatSessionResponse:
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        message_count=len(session.messages),
    )


def _message_response(msg: ChatMessage) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=msg.id,
        role=msg.role,
        content=msg.content,
        created_at=msg.created_at.isoformat(),
    )


def _load_user_profile(db: Session, user_id: int) -> UserProfile | None:
    row = db.query(UserFinancialProfile).filter(UserFinancialProfile.user_id == user_id).first()
    if row and row.profile_json and row.profile_json != "{}":
        return UserProfile.model_validate_json(row.profile_json)
    return None


def _load_user_analysis(db: Session, user_id: int) -> dict | None:
    row = db.query(UserFinancialProfile).filter(UserFinancialProfile.user_id == user_id).first()
    if row and row.last_analysis_json:
        return json.loads(row.last_analysis_json)
    return None


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
        .limit(50)
        .all()
    )
    return [_session_response(s) for s in sessions]


@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = ChatSession(user_id=user.id, title="New conversation")
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_response(session)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def get_messages(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return [_message_response(m) for m in session.messages]


@router.post("/sessions/{session_id}/messages", response_model=ChatSendResponse)
def send_message(
    session_id: int,
    body: ChatSendRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = ChatMessage(session_id=session.id, role="user", content=body.content)
    db.add(user_msg)
    db.flush()

    profile = _load_user_profile(db, user.id)
    analysis = _load_user_analysis(db, user.id)
    history = [{"role": m.role, "content": m.content} for m in session.messages[-9:]]
    history.append({"role": "user", "content": body.content})
    answer = _advisor.chat_with_history(profile, body.content, history, user.name, analysis)

    assistant_msg = ChatMessage(session_id=session.id, role="assistant", content=answer)
    db.add(assistant_msg)

    if session.title == "New conversation" or len(session.messages) <= 1:
        session.title = body.content[:60] + ("…" if len(body.content) > 60 else "")
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)

    return ChatSendResponse(
        user_message=_message_response(user_msg),
        assistant_message=_message_response(assistant_msg),
        session_id=session.id,
    )


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"deleted": session_id}
