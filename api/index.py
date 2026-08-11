"""Expose the FastAPI ASGI application to Vercel's Python runtime."""

from app.main import app

__all__ = ["app"]
