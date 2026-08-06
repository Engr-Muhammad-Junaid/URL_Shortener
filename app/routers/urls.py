import random
import string
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter()


# --- Helper function to generate short code ---
def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


# --- Create a short URL ---
@router.post("/urls", response_model=schemas.URLResponse)
def create_url(payload: schemas.URLCreate, db: Session = Depends(get_db)):
    # Keep generating until we get a unique code
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
    return new_url


# --- Redirect to original URL ---
@router.get("/{short_code}")
def redirect_url(short_code: str, db: Session = Depends(get_db)):
    url = db.query(models.URL).filter(models.URL.short_code == short_code).first()

    if not url:
        raise HTTPException(status_code=404, detail="URL not found")

    url.clicks += 1
    db.commit()

    return RedirectResponse(url=url.original_url)


# --- Get all URLs ---
@router.get("/urls/all", response_model=list[schemas.URLResponse])
def get_all_urls(db: Session = Depends(get_db)):
    urls = db.query(models.URL).all()
    return urls


# --- Delete a URL ---
@router.delete("/urls/{id}")
def delete_url(id: int, db: Session = Depends(get_db)):
    url = db.query(models.URL).filter(models.URL.id == id).first()

    if not url:
        raise HTTPException(status_code=404, detail="URL not found")

    db.delete(url)
    db.commit()

    return {"message": "URL deleted successfully"}
