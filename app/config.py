from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str
    ADMIN_PASSWORD: str
    SESSION_SECRET: str
    APP_NAME: str = "URL Shortener"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

# Single instance used across the entire app
settings = Settings()
