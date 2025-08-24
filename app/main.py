# app/main.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth as auth_router
from .routers import todos as todos_router
from .routers import pomodoro as pomodoro_router
from .routers import todos as todos_router
from dotenv import load_dotenv; load_dotenv()


# Create DB tables once on startup (better to use Alembic later)
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

# Single FastAPI app
app = FastAPI(title="Todo + Time Manager", version="1.1.0", lifespan=lifespan)

# CORS: read comma-separated origins from env, with sensible defaults
env_origins = os.getenv("CORS_ORIGINS", "").strip()
default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
origins = [o.strip() for o in env_origins.split(",") if o.strip()] or default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router.router)
app.include_router(todos_router.router)
app.include_router(pomodoro_router.router)

# Friendly root + health
@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "API is running (with auth)",
        "routes": ["/auth/*", "/todos/*", "/pomodoro/*", "/docs", "/openapi.json"]
    }

@app.get("/health", include_in_schema=False)
def health():
    return {"ok": True}
