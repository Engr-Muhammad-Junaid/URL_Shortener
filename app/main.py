from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.routers import urls
from app.config import settings
from app.logger import setup_logger
from app.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    global_exception_handler
)

# Setup logger
logger = setup_logger()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Include routers
app.include_router(urls.router)


# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME
    }


logger.info(f"{settings.APP_NAME} started")
