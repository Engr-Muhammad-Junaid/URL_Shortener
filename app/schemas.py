from pydantic import BaseModel, HttpUrl
from datetime import datetime


# What the user sends us
class URLCreate(BaseModel):
    original_url: HttpUrl


# What we send back
class URLResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    clicks: int
    created_at: datetime

    class Config:
        from_attributes = True
