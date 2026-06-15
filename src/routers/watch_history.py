from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.dependencies import get_db, get_current_user
from src.models.models import WatchHistory, Content, Episode
from src.models.schemas import WatchHistoryCreate, WatchHistoryResponse

router = APIRouter(prefix="/watch-history", tags=["Watch History"])


@router.post("/", response_model=WatchHistoryResponse, status_code=201)
def register_watch(
    watch: WatchHistoryCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
   
    content = db.query(Content).filter(Content.id == watch.content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")

    if watch.episode_id:
        episode = db.query(Episode).filter(Episode.id == watch.episode_id).first()
        if not episode:
            raise HTTPException(status_code=404, detail="Episodio no encontrado")

   
    query = db.query(WatchHistory).filter(
        WatchHistory.user_id == current_user.id,
        WatchHistory.content_id == watch.content_id,
    )
    if watch.episode_id:
        query = query.filter(WatchHistory.episode_id == watch.episode_id)

    existing = query.first()

    if existing:
      
        existing.progress_seconds = watch.progress_seconds
        existing.completed = watch.progress_seconds >= (
            episode.duration_seconds if watch.episode_id else content.duration_seconds or 0
        ) * 0.9  
        db.commit()
        db.refresh(existing)
        return existing


    new_watch = WatchHistory(
        user_id=current_user.id,
        content_id=watch.content_id,
        episode_id=watch.episode_id,
        progress_seconds=watch.progress_seconds,
        completed=False
    )
    db.add(new_watch)
    db.commit()
    db.refresh(new_watch)
    return new_watch


@router.get("/", response_model=List[WatchHistoryResponse])
def get_watch_history(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    history = db.query(WatchHistory).filter(
        WatchHistory.user_id == current_user.id
    ).order_by(WatchHistory.watched_at.desc()).all()
    return history


@router.get("/{content_id}", response_model=WatchHistoryResponse)
def get_content_progress(
    content_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    watch = db.query(WatchHistory).filter(
        WatchHistory.user_id == current_user.id,
        WatchHistory.content_id == content_id
    ).order_by(WatchHistory.watched_at.desc()).first()

    if not watch:
        raise HTTPException(status_code=404, detail="No hay progreso registrado para este contenido")
    return watch


@router.delete("/{watch_id}", status_code=204)
def delete_watch_record(
    watch_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    watch = db.query(WatchHistory).filter(
        WatchHistory.id == watch_id,
        WatchHistory.user_id == current_user.id
    ).first()

    if not watch:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    db.delete(watch)
    db.commit()