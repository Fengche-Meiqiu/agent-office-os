from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.seed import init_seed_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[startup] initializing database")
    init_db()
    print("[startup] loading seed data when needed")
    init_seed_data()
    print(f"[startup] {settings.APP_NAME} ready on http://localhost:{settings.PORT}")
    yield
    print("[shutdown] application stopped")


app = FastAPI(
    title=settings.APP_NAME,
    description="Agent Office OS backend API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import chat, event_logs, marketplace, meetings, office, outputs, tasks, webhook

app.include_router(marketplace.router)
app.include_router(office.router)
app.include_router(chat.router)
app.include_router(tasks.router)
app.include_router(meetings.router)
app.include_router(outputs.router)
app.include_router(webhook.router)
app.include_router(event_logs.router)


@app.get("/api/health", tags=["system"])
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}


@app.get("/", tags=["system"])
async def root():
    return {"message": "Agent Office OS API", "docs": "/docs"}
