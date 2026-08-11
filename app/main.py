from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.routers import urls
from app.config import settings
from app.auth import (
    COOKIE_NAME,
    SESSION_LIFETIME_SECONDS,
    create_session_token,
    is_valid_session,
    password_is_valid,
)
from app.logger import setup_logger
from app.limiter import limiter
from fastapi.middleware.cors import CORSMiddleware

from app.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    global_exception_handler
)

logger = setup_logger()
FRONTEND_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    description="A production-ready URL shortener API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Serve the browser UI alongside the API. Keeping both on one origin means the
# frontend always talks to the exact backend instance that served it.
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard(request: Request):
    if not is_valid_session(request.cookies.get(COOKIE_NAME)):
        return RedirectResponse("/login", status_code=303)
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/login", include_in_schema=False)
def login_page(request: Request):
    if is_valid_session(request.cookies.get(COOKIE_NAME)):
        return RedirectResponse("/dashboard", status_code=303)
    return FileResponse(FRONTEND_DIR / "login.html")


@app.post("/admin/login", include_in_schema=False)
@limiter.limit("5/minute")
async def admin_login(request: Request, response: Response):
    payload = await request.json()
    if not password_is_valid(str(payload.get("password", ""))):
        raise AppException(status_code=401, message="Incorrect password")
    response.set_cookie(
        COOKIE_NAME,
        create_session_token(),
        max_age=SESSION_LIFETIME_SECONDS,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="strict",
        path="/",
    )
    return {"message": "Login successful"}


@app.post("/admin/logout", include_in_schema=False)
def admin_logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"message": "Logged out"}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0"
    }


# Keep the catch-all /{short_code} router after fixed application routes.
app.include_router(urls.router)


logger.info(f"{settings.APP_NAME} started")
