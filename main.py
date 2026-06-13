from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from src.models.schemas import UserRegistration, UserLogin, UserResponse, tokenResponse
from src.auth.auth import hash_password, verify_password, create_access_token, decode_token, ACCESS_TOKEN_EXPIRE_MINUTES
from database import test_connection, create_tables, Session as SessionLocal
from src.models.content import Subscription, SubscriptionPlan, User
from src.models.schemas import SubscriptionPlanCreate, SubscriptionPlanResponse
from src.models.schemas import SubscriptionCreate 
from src.models.schemas import SubscriptionResponse

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup():
    test_connection()
    create_tables()

# ========== AUTENTICACIÓN ==========



@app.post("/register", response_model=UserResponse)
def register(user: UserRegistration, db: Session = Depends(get_db)):
    """Registra un nuevo usuario"""
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    
    new_user = User(
        email=user.email,
        is_admin=user.is_admin,
        password_hash=hash_password(user.password),
        full_name=user.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def is_admin_user(current_user: User) -> bool:
    """Verifica si el usuario es admin"""
    return current_user.is_admin

@app.post("/login", response_model=tokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    
    # Verificar suscripción activa
    active_sub = get_active_subscription(db_user.id, db)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:

    """Obtiene el usuario actual del token"""

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
@app.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):

    """Obtiene info del usuario actual (protegido)"""

    return current_user

@app.put("/user", response_model=UserResponse)
def update_user(full_name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Actualiza el usuario (protegido)"""
    current_user.full_name = full_name
    db.commit()
    db.refresh(current_user)
    return current_user

@app.delete("/user", status_code=204)
def delete_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Elimina el usuario (protegido)"""
    db.delete(current_user)
    db.commit()

@app.get("/")
def root():
    return {"message": "API Streamdb"}


# ========== Suscripción plan ==========


@app.post("/subscription-plans", response_model=SubscriptionPlanResponse, status_code=201)
def create_subscription_plan(
    plan: SubscriptionPlanCreate,
    current_user: User = Depends(get_current_user),
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

@app.get("/subscription-plans", response_model=list[SubscriptionPlanResponse])
def list_subscription_plans(db: Session = Depends(get_db)):
    """Lista todos los planes de suscripción activos"""
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()
    return plans

@app.get("/subscription-plans/{plan_id}", response_model=SubscriptionPlanResponse)
def get_subscription_plan(plan_id: str, db: Session = Depends(get_db)):
    
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de suscripción no encontrado")
    return plan

@app.put("/subscription-plans/{plan_id}", response_model=SubscriptionPlanResponse)
def update_subscription_plan(
    plan_id: str,
    plan_update: SubscriptionPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de suscripción no encontrado")
    
    plan.name = plan_update.name
    plan.price = plan_update.price
    plan.quality = plan_update.quality
    plan.max_screens = plan_update.max_screens
    
    db.commit()
    db.refresh(plan)
    return plan

@app.delete("/subscription-plans/{plan_id}", status_code=204)
def delete_subscription_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    # Verificar que el usuario sea admin
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de suscripción no encontrado")
    
    db.delete(plan)
    db.commit()


# ========== Suscripciones ==========

@app.post("/subscriptions", response_model=SubscriptionResponse, status_code=201)
def create_subscription(
    subscription: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
      
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de suscripción no encontrado")
    
 
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

@app.get("/subscriptions", response_model=list[SubscriptionResponse])
def list_subscriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    subscriptions = db.query(Subscription).filter(Subscription.user_id == current_user.id).all()
    return subscriptions

@app.put("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
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

@app.get("/subscriptions/active", response_model=SubscriptionResponse)
def get_user_active_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene la suscripción activa del usuario"""
    subscription = get_active_subscription(current_user.id, db)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No tienes una suscripción activa")
    
    return subscription