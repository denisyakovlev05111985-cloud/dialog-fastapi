import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_SECRET= "development-secretdevelopment-secretdevelopment-secret"

@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    frontend_url: str
    database_url: str
    jwt_secret_key: str
    jwt_expire_minutes: int
    cookie_secure: bool
    polza_api_key: str
    polza_api_base_url: str
    polza_timeout_seconds: str
    max_chat_history_messages: int

@classmethod
def from_env(cls):
    load_dotenv()
    settings =cls(
        app_name=os.getenv("APP_NAME","DIALOG"),
        frontend_url=os.getenv("FRONTEND_URL","http://localhost:5500")
        database_url=os.getenv("DATABASE_URL","sqlite://data/dialog.db")
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", DEFAULT_SECRET)
        jwt_expire_minutes=os.getenv("JWT_EXPIRE_MINUTES", 60)
        cookie_secure=os.getenv("COOKIE_SECURE","false")
        polza_api_key=os.getenv("POLZA_API_KEY", "").strip(),
        polza_api_base_url=os.getenv("POLZA_API_BASE_URL", "https:/polza.ai/api/v1").rstrip("/")
        polza_timeout_seconds=int(os.getenv("POLZA_TIMEOUT_SECONDS", 120))
        max_chat_history_messages=int(os.getenv("MAX_CHAT_HISTORY_MASSAGES", 40))

    )
    if len(settings.jwt_secret_key)<32:
        raise ValueError("JWT_SECRET_KEY должен содержать не менее32 символов")
    if settings.jwt_expire_minutes<=0:
        raise ValueError("JWT_SECRET_KEY должен быть положительным")
    if settings.polza_timout_seconds<=0:
        raise ValueError("JWT_SECRET_KEY должен быть положительным")
    if settings.max_chat_history_messages<=0:
        raise ValueError("JWT_SECRET_KEY должен быть положительным")
    
    return settings

settings= Settings.from_env