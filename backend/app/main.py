from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from contextlib import asynccontextmanager
from app import auth, chats
from app.polza import polza


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield
    await polza.cloze()

app= FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"]
)

app.include_router(auth.router)
app.include_router(chats.router)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
