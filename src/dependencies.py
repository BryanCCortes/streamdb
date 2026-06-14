from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from database import Session as SessionLocal
from src.auth.auth import decode_token
from src.Models.models import User, Subscription


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")

    token = authorization.replace("Bearer ", "")
    email = decode_token(token)

    if email is None:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return user


def is_admin_user(current_user: User) -> bool:
    return current_user.is_admin


def get_active_subscription(user_id: UUID, db: Session) -> Optional[Subscription]:
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status == "active",
        Subscription.starts_at <= datetime.utcnow()
    ).first()

    if subscription and subscription.ends_at:
        if subscription.ends_at < datetime.utcnow():
            subscription.status = "expired"
            db.commit()
            return None

    return subscription