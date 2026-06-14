from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.dependencies import get_db, get_current_user, is_admin_user
from src.Models.models import Genre
from src.Models.schemas import GenreCreate, GenreResponse

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.post("/", response_model=GenreResponse, status_code=201)
def create_genre(
    genre: GenreCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    new_genre = Genre(name=genre.name)
    db.add(new_genre)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="El género ya existe")
    db.refresh(new_genre)
    return new_genre


@router.get("/", response_model=list[GenreResponse])
def list_genres(db: Session = Depends(get_db)):
    return db.query(Genre).all()


@router.get("/{genre_id}", response_model=GenreResponse)
def get_genre(genre_id: str, db: Session = Depends(get_db)):
    genre = db.query(Genre).filter(Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Género no encontrado")
    return genre


@router.put("/{genre_id}", response_model=GenreResponse)
def update_genre(
    genre_id: str,
    genre_update: GenreCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    genre = db.query(Genre).filter(Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Género no encontrado")

    genre.name = genre_update.name
    db.commit()
    db.refresh(genre)
    return genre