from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from typing import Literal


# ========== USER ==========
class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    is_admin: Optional[bool] = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class tokenResponse(BaseModel):
    access_token: str
    token_type: str

# ========== GENRE ==========
class GenreCreate(BaseModel):
    name: str

class GenreResponse(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True



# ========== EPISODE ==========
class EpisodeCreate(BaseModel):
    episode_number: int
    title: str
    duration_seconds: Optional[int] = None
    video_url: Optional[str] = None

class EpisodeResponse(BaseModel):
    id: UUID
    season_id: UUID
    episode_number: int
    title: str
    duration_seconds: Optional[int] = None
    video_url: Optional[str] = None

    class Config:
        from_attributes = True

# ========== SEASON ==========
class SeasonCreate(BaseModel):
    
    season_number: int
    title: Optional[str] = None

class SeasonResponse(BaseModel):
    id: UUID
    content_id: UUID
    season_number: int
    title: Optional[str] = None
    episodes: List[EpisodeResponse] = []   

    class Config:
        from_attributes = True


# ========== CONTENT ==========
class ContentCreate(BaseModel):
    title: str
    type: Literal["movie", "series"]
    description: Optional[str] = None
    is_premium: Optional[bool] = False
    release_year: Optional[int] = None
    avg_rating: Optional[float] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None


class ContentResponse(BaseModel):
    id: UUID
    title: str
    type: Literal["movie", "series"]
    description: Optional[str] = None
    is_premium: bool
    release_year: Optional[int] = None
    avg_rating: Optional[float] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    is_active: bool
    genres: List[GenreResponse] = []       
    seasons: List[SeasonResponse] = []     

    class Config:
        from_attributes = True



# ========== SUBSCRIPTION PLAN ==========
class SubscriptionPlanCreate(BaseModel):
    name: str
    price: float
    quality: str  #ejemplo 'SD', 'HD', '4K'
    max_screens: int

class SubscriptionPlanResponse(BaseModel):
    id: UUID
    name: str
    price: float
    quality: str
    max_screens: int
    is_active: bool

    class Config:
        from_attributes = True

# ========== SUBSCRIPTION ==========
class SubscriptionCreate(BaseModel):
    
    plan_id: UUID

class SubscriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    plan_id: UUID
    status: str
    starts_at: datetime
    ends_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ========== WATCH HISTORY ==========
class WatchHistoryCreate(BaseModel):
    content_id: UUID
    episode_id: Optional[UUID] = None
    progress_seconds: int

class WatchHistoryResponse(BaseModel):
    id: UUID
    user_id: UUID
    content_id: UUID
    episode_id: Optional[UUID] = None
    progress_seconds: int
    completed: bool
    watched_at: datetime

    class Config:
        from_attributes = True

# ========== WATCHLIST ==========
class WatchlistCreate(BaseModel):
    content_id: UUID

class WatchlistResponse(BaseModel):
    id: UUID
    user_id: UUID
    content_id: UUID
    added_at: datetime

    class Config:
        from_attributes = True