import random
import string
import ipaddress
import math
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from loguru import logger
from app.database import get_db
from app import models, schemas
from app.exceptions import AppException
from app.limiter import limiter
from app.auth import require_admin

router = APIRouter()


def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


def validate_public_destination(value: str) -> None:
    """Reject destinations that point directly at local/private infrastructure."""
    parsed = urlsplit(value)
    hostname = (parsed.hostname or "").rstrip(".").lower()
    if parsed.username or parsed.password:
        raise AppException(status_code=422, message="URLs containing credentials are not allowed")
    if hostname == "localhost" or hostname.endswith((".localhost", ".local")):
        raise AppException(status_code=422, message="Local network URLs are not allowed")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return
    if not address.is_global:
        raise AppException(status_code=422, message="Private or reserved IP addresses are not allowed")


# 10 URLs per minute per IP
@router.post("/urls", response_model=schemas.URLResponse)
@limiter.limit("10/minute")
def create_url(request: Request, payload: schemas.URLCreate, db: Session = Depends(get_db)):
    original_url = str(payload.original_url)
    validate_public_destination(original_url)

    existing = db.query(models.URL).filter(models.URL.original_url == original_url).first()
    if existing:
        logger.info(f"Reused short URL: {existing.short_code} → {original_url}")
        return existing

    while True:
        code = generate_short_code()
        exists = db.query(models.URL).filter(models.URL.short_code == code).first()
        if not exists:
            break

    new_url = models.URL(
        original_url=original_url,
        short_code=code
    )
    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    logger.info(f"Created short URL: {code} → {payload.original_url}")
    return new_url


@router.get("/admin/urls", response_model=schemas.URLPage)
@limiter.limit("30/minute")
def get_url_page(
    request: Request,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 25,
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    total = db.query(models.URL).count()
    items = (
        db.query(models.URL)
        .order_by(models.URL.created_at.desc(), models.URL.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total else 0,
    }


@router.post("/admin/urls/cleanup")
@limiter.limit("2/minute")
def cleanup_urls(
    request: Request,
    payload: schemas.CleanupRequest,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=payload.older_than_days)
    deleted = db.query(models.URL).filter(models.URL.created_at < cutoff).delete(synchronize_session=False)
    db.commit()
    logger.info(f"Cleaned up {deleted} URLs older than {payload.older_than_days} days")
    return {"message": "Cleanup completed", "deleted": deleted}


# 30 requests per minute per IP
@router.get("/urls/all", response_model=list[schemas.URLResponse])
@limiter.limit("30/minute")
def get_all_urls(
    request: Request,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    urls = db.query(models.URL).offset(skip).limit(limit).all()
    logger.info(f"Fetched URLs: skip={skip} limit={limit} returned={len(urls)}")
    return urls

# 10 deletes per minute per IP
@router.delete("/urls/{id}")
@limiter.limit("10/minute")
def delete_url(
    request: Request,
    id: int,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    url = db.query(models.URL).filter(models.URL.id == id).first()

    if not url:
        logger.warning(f"Delete failed — URL id {id} not found")
        raise AppException(status_code=404, message=f"URL with id {id} not found")

    db.delete(url)
    db.commit()

    logger.info(f"Deleted URL id: {id}")
    return {"message": "URL deleted successfully"}


# Keep the dynamic short-code route last so it cannot shadow fixed API paths.
@router.get("/{short_code}")
@limiter.limit("30/minute")
def redirect_url(request: Request, short_code: str, db: Session = Depends(get_db)):
    url = db.query(models.URL).filter(models.URL.short_code == short_code).first()

    if not url:
        logger.warning(f"Short code not found: {short_code}")
        raise AppException(status_code=404, message=f"Short code '{short_code}' not found")

    url.clicks += 1
    db.commit()

    logger.info(f"Redirecting {short_code} → {url.original_url} (clicks: {url.clicks})")
    return RedirectResponse(url=url.original_url)
