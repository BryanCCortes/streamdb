from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.dependencies import get_db, get_current_user, is_admin_user, get_active_subscription
from src.models.models import Subscription, SubscriptionPlan
from src.models.schemas import (
    SubscriptionCreate, SubscriptionResponse,
    SubscriptionPlanCreate, SubscriptionPlanResponse
)

router = APIRouter(tags=["Subscriptions"])


# ── Planes ──────────────────────────────────────────────

@router.post("/subscription-plans", response_model=SubscriptionPlanResponse, status_code=201)
def create_subscription_plan(
    plan: SubscriptionPlanCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    new_plan = SubscriptionPlan(
        name=plan.name,
        price=plan.price,
        quality=plan.quality,
        max_screens=plan.max_screens
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan


@router.get("/subscription-plans", response_model=list[SubscriptionPlanResponse])
def list_subscription_plans(db: Session = Depends(get_db)):
    return db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()


@router.get("/subscription-plans/{plan_id}", response_model=SubscriptionPlanResponse)
def get_subscription_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan


@router.put("/subscription-plans/{plan_id}", response_model=SubscriptionPlanResponse)
def update_subscription_plan(
    plan_id: str,
    plan_update: SubscriptionPlanCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    plan.name = plan_update.name
    plan.price = plan_update.price
    plan.quality = plan_update.quality
    plan.max_screens = plan_update.max_screens

    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/subscription-plans/{plan_id}", status_code=204)
def delete_subscription_plan(
    plan_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    db.delete(plan)
    db.commit()


# ── Suscripciones ────────────────────────────────────────

@router.post("/subscriptions", response_model=SubscriptionResponse, status_code=201)
def create_subscription(
    subscription: SubscriptionCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    if not plan.is_active:
        raise HTTPException(status_code=400, detail="Este plan no está disponible")

    new_subscription = Subscription(
        user_id=current_user.id,
        plan_id=subscription.plan_id,
        ends_at=datetime.utcnow() + timedelta(days=30),
        status="active"
    )
    db.add(new_subscription)
    db.commit()
    db.refresh(new_subscription)
    return new_subscription


@router.get("/subscriptions", response_model=list[SubscriptionResponse])
def list_subscriptions(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Subscription).filter(Subscription.user_id == current_user.id).all()


@router.get("/subscriptions/active", response_model=SubscriptionResponse)
def get_user_active_subscription(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subscription = get_active_subscription(current_user.id, db)
    if not subscription:
        raise HTTPException(status_code=404, detail="No tienes una suscripción activa")
    return subscription


@router.put("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    subscription_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    if subscription.status != "active":
        raise HTTPException(status_code=400, detail="Solo se pueden cancelar suscripciones activas")

    subscription.status = "cancelled"
    subscription.ends_at = datetime.utcnow()
    db.commit()
    db.refresh(subscription)
    return subscription