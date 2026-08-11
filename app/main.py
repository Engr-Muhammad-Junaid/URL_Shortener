from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.routers import urls
from app.config import settings
from app.logger import setup_logger
from app.limiter import limiter
from app.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    global_exception_handler
)

logger = setup_logger()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    description="A production-ready URL shortener API",
    version="1.0.0"
)

# Attach limiter to app
app.state.limiter = limiter

# Register all exception handlers
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Add rate limiting middleware
app.add_middleware(SlowAPIMiddleware)

# Include routers
app.include_router(urls.router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0"
    }


logger.info(f"{settings.APP_NAME} started")
