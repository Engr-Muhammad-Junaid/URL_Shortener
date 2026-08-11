import random
import string
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from loguru import logger
from app.database import get_db
from app import models, schemas
from app.exceptions import AppException

router = APIRouter()


def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


@router.post("/urls", response_model=schemas.URLResponse)
def create_url(payload: schemas.URLCreate, db: Session = Depends(get_db)):
    while True:
        code = generate_short_code()
        exists = db.query(models.URL).filter(models.URL.short_code == code).first()
        if not exists:
            break

    new_url = models.URL(
        original_url=str(payload.original_url),
        short_code=code
    )
    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    logger.info(f"Created short URL: {code} → {payload.original_url}")
    return new_url


@router.get("/{short_code}")
def redirect_url(short_code: str, db: Session = Depends(get_db)):
    url = db.query(models.URL).filter(models.URL.short_code == short_code).first()

    if not url:
        logger.warning(f"Short code not found: {short_code}")
        raise AppException(status_code=404, message=f"Short code '{short_code}' not found")

    url.clicks += 1
    db.commit()

    logger.info(f"Redirecting {short_code} → {url.original_url} (clicks: {url.clicks})")
    return RedirectResponse(url=url.original_url)


@router.get("/urls/all", response_model=list[schemas.URLResponse])
def get_all_urls(db: Session = Depends(get_db)):
    urls = db.query(models.URL).all()
    logger.info(f"Fetched all URLs: {len(urls)} records")
    return urls


@router.delete("/urls/{id}")
def delete_url(id: int, db: Session = Depends(get_db)):
    url = db.query(models.URL).filter(models.URL.id == id).first()

    if not url:
        logger.warning(f"Delete failed — URL id {id} not found")
        raise AppException(status_code=404, message=f"URL with id {id} not found")

    db.delete(url)
    db.commit()

    logger.info(f"Deleted URL id: {id}")
    return {"message": "URL deleted successfully"}
