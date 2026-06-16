from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.dependencies import get_db, get_current_user, is_admin_user
from src.models.models import Content, Season, Episode
from src.models.schemas import (
    ContentCreate, ContentResponse,
    SeasonCreate, SeasonResponse,
    EpisodeCreate, EpisodeResponse
)
from src.dependencies import access_premium_content
from src.models.models import Genre

router = APIRouter(tags=["Content"])


# ── Contenido ────────────────────────────────────────────

@router.post("/content", response_model=ContentResponse, status_code=201)
def create_content(
    content: ContentCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    if not content.genre_ids:
        raise HTTPException(status_code=400, detail="El contenido debe tener al menos un género")

    found_genres = db.query(Genre).filter(Genre.id.in_(content.genre_ids)).all()

    if len(found_genres) != len(content.genre_ids):
        raise HTTPException(status_code=404, detail="Uno o más géneros no existen")

    new_content = Content(
    title=content.title,
    type=content.type,
    description=content.description,
    is_premium=content.is_premium,
    release_year=content.release_year,
    avg_rating=content.avg_rating,
    poster_url=content.poster_url,
    backdrop_url=content.backdrop_url,
    genres=found_genres
)
    db.add(new_content)
    db.flush()  

    if content.type == "movie" and content.seasons:
        raise HTTPException(status_code=400, detail="Solo las series pueden tener temporadas")

    if content.type == "series":
        for season_data in content.seasons:
            new_season = Season(
                content_id=new_content.id,
                season_number=season_data.season_number,
                title=season_data.title
            )
            db.add(new_season)  
        
    db.commit()
    db.refresh(new_content)
    return new_content

@router.get("/content", response_model=List[ContentResponse])
def list_content(
    genre: str | None = None,
    type: str | None = None,
    is_premium: bool | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Content).filter(Content.is_active == True)

    if genre is not None:
        query = query.filter(Content.genres.any(name=genre))

    if is_premium is not None:
        query = query.filter(Content.is_premium == is_premium)

    if type is not None:
        query = query.filter(Content.type == type)

    return query.all()


@router.get("/content/{content_id}", response_model=ContentResponse)
def get_content(
    content_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    
    access_premium_content(content, current_user, db)
    return content


@router.put("/content/{content_id}", response_model=ContentResponse)
def update_content(
    content_id: str,
    content_update: ContentCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")

    content.title = content_update.title
    content.type = content_update.type
    content.description = content_update.description
    content.is_premium = content_update.is_premium
    content.release_year = content_update.release_year
    content.avg_rating = content_update.avg_rating
    content.poster_url = content_update.poster_url
    content.backdrop_url = content_update.backdrop_url

    db.commit()
    db.refresh(content)
    return content

@router.delete("/content/{content_id}", status_code=204)
def delete_content(
    content_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")

    content.is_active = False
    db.commit()

# ── Temporadas ───────────────────────────────────────────

@router.post("/content/{content_id}/seasons", response_model=SeasonResponse, status_code=201)
def create_season(
    content_id: str,
    season: SeasonCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    if content.type != "series":
        raise HTTPException(status_code=400, detail="Solo las series tienen temporadas")

    new_season = Season(
        content_id=content_id,
        season_number=season.season_number,
        title=season.title
    )
    db.add(new_season)
    db.commit()
    db.refresh(new_season)
    return new_season


@router.get("/content/{content_id}/seasons", response_model=List[SeasonResponse])
def list_seasons(content_id: str, db: Session = Depends(get_db)):
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    return content.seasons


# ── Episodios ────────────────────────────────────────────

@router.post("/seasons/{season_id}/episodes", response_model=List[EpisodeResponse], status_code=201)
def create_episode(
    season_id: str,
    episodes: List[EpisodeCreate],
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    season = db.query(Season).filter(Season.id == season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Temporada no encontrada")

    new_episodes = []
    for episode in episodes:
        new_episode = Episode(
            season_id=season_id,
            episode_number=episode.episode_number,
            title=episode.title,
            duration_seconds=episode.duration_seconds,
            video_url=episode.video_url
        )
        db.add(new_episode)
        new_episodes.append(new_episode)

    db.commit()
    return new_episodes

@router.get("/seasons/{season_id}/episodes", response_model=List[EpisodeResponse])
def list_episodes(season_id: str, db: Session = Depends(get_db)):
    season = db.query(Season).filter(Season.id == season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Temporada no encontrada")
    return season.episodes
