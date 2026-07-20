from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app= FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"]
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
