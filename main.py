from fastapi import FastAPI
from database import test_connection, create_tables
from src.routers import auth, suscriptions, genres, content

app = FastAPI(
    title="StreamDB API",
    description="REST API for a streaming platform built with FastAPI and PostgreSQL",
    version="0.1.0"
)

@app.on_event("startup")
def startup():
    test_connection()
    create_tables()

@app.get("/")
def root():
    return {"message": "StreamDB API"}

app.include_router(auth.router)
app.include_router(suscriptions.router)
app.include_router(genres.router)
app.include_router(content.router)