from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str
    ADMIN_PASSWORD: str
    SESSION_SECRET: str
    APP_NAME: str = "URL Shortener"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"



# Single instance used across the entire app
settings = Settings()
