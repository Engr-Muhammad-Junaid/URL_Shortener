from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger


# Custom exception class
class AppException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


# Handler for our custom exceptions
async def app_exception_handler(request: Request, exc: AppException):
    logger.error(f"{request.method} {request.url} - {exc.status_code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "status_code": exc.status_code
        }
    )


# Handler for Pydantic validation errors
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " → ".join(str(e) for e in error["loc"]),
            "message": error["msg"]
        })

    logger.warning(f"{request.method} {request.url} - 422 - Validation error: {errors}")

    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation failed",
            "details": errors,
            "status_code": 422
        }
    )


# Handler for unhandled exceptions (catch-all)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {request.method} {request.url} - {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500
        }
    )
