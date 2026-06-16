from typing import Optional
from uuid import UUID
from datetime import datetime
from src.models.models import User, Subscription, Content
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer
from database import Session as SessionLocal
from src.auth.auth import decode_token
from src.models.models import User, Subscription, Content



security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_current_user(
    credentials=Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
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

def access_premium_content(content, current_user: User, db: Session):
    if content.is_premium:
        subscription = get_active_subscription(current_user.id, db)
        if not subscription:
            raise HTTPException(
                status_code=403,
                detail="Se requiere una suscripción activa para acceder a este contenido"
            )