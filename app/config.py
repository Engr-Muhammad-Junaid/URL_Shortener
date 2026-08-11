from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    APP_NAME: str = "URL Shortener"
    DEBUG: bool = False

    class Config:
        env_file = ".env"


# Single instance used across the entire app
settings = Settings()
