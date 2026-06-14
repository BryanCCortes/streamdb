import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean,
    ForeignKey, DateTime, UniqueConstraint, Table
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


# ──────────────────────────────────────────
# Tabla pivote content_genres
# ──────────────────────────────────────────

content_genres_table = Table(
    "content_genres",
    Base.metadata,
    Column("content_id", ForeignKey("content.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True),
)


# ──────────────────────────────────────────
# Usuarios y suscripciones
# ──────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    is_admin      = Column(Boolean, default=False, nullable=False)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(255), nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscriptions = relationship("Subscription", back_populates="user")
    watch_history = relationship("WatchHistory", back_populates="user")
    watchlist     = relationship("Watchlist", back_populates="user")


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name        = Column(String(100), nullable=False)
    price       = Column(Float, nullable=False)
    quality     = Column(String(10), nullable=False)
    max_screens = Column(Integer, nullable=False, default=1)
    is_active   = Column(Boolean, default=True)

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan_id    = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    status     = Column(String(20), nullable=False, default="active")
    starts_at  = Column(DateTime, nullable=False, default=datetime.utcnow)
    ends_at    = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")


# ──────────────────────────────────────────
# Catálogo
# ──────────────────────────────────────────

class Genre(Base):
    __tablename__ = "genres"

    id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)

    contents = relationship("Content", secondary=content_genres_table, back_populates="genres")


class Content(Base):
    __tablename__ = "content"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title        = Column(String(255), nullable=False, index=True)
    type         = Column(String(20), nullable=False)
    description  = Column(Text, nullable=True)
    is_premium   = Column(Boolean, default=False, nullable=False)
    release_year = Column(Integer, nullable=True)
    avg_rating   = Column(Float, nullable=True)
    poster_url   = Column(String(500), nullable=True)
    backdrop_url = Column(String(500), nullable=True)
    is_active    = Column(Boolean, default=True, nullable=False)

    genres        = relationship("Genre", secondary=content_genres_table, back_populates="contents")
    seasons       = relationship("Season", back_populates="content")
    watch_history = relationship("WatchHistory", back_populates="content")
    watchlist     = relationship("Watchlist", back_populates="content")


class Season(Base):
    __tablename__ = "seasons"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id    = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    season_number = Column(Integer, nullable=False)
    title         = Column(String(255), nullable=True)

    content  = relationship("Content", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season")


class Episode(Base):
    __tablename__ = "episodes"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    season_id        = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=False)
    episode_number   = Column(Integer, nullable=False)
    title            = Column(String(255), nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    video_url        = Column(String(500), nullable=True)

    season        = relationship("Season", back_populates="episodes")
    watch_history = relationship("WatchHistory", back_populates="episode")


# ──────────────────────────────────────────
# Actividad del usuario
# ──────────────────────────────────────────

class WatchHistory(Base):
    __tablename__ = "watch_history"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id          = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content_id       = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    episode_id       = Column(UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=True)
    progress_seconds = Column(Integer, default=0, nullable=False)
    completed        = Column(Boolean, default=False, nullable=False)
    watched_at       = Column(DateTime, default=datetime.utcnow, nullable=False)

    user    = relationship("User", back_populates="watch_history")
    content = relationship("Content", back_populates="watch_history")
    episode = relationship("Episode", back_populates="watch_history")


class Watchlist(Base):
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint("user_id", "content_id"),)

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content.id"), nullable=False)
    added_at   = Column(DateTime, default=datetime.utcnow, nullable=False)

    user    = relationship("User", back_populates="watchlist")
    content = relationship("Content", back_populates="watchlist")