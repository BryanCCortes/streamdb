from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.dependencies import get_db, get_current_user
from src.Models.models import Watchlist, Content
from src.Models.schemas import WatchlistCreate, WatchlistResponse

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

@router.post("/", response_model=WatchlistResponse, status_code=201)
def add_to_watchlist(
    item: WatchlistCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = db.query(Content).filter(Content.id == item.content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")


    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.content_id == item.content_id,
        
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Ya está en la watchlist")

    new_item = Watchlist(
        user_id=current_user.id,
        content_id=item.content_id,
        
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.get("/", response_model=List[WatchlistResponse])
def get_watchlist(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()

@router.delete("/{item_id}", status_code=204)
def remove_from_watchlist(
    item_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(Watchlist).filter(
        Watchlist.id == item_id,
        Watchlist.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Elemento no encontrado en la watchlist")

    db.delete(item)
    db.commit()